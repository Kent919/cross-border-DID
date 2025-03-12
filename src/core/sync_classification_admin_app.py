from flask import Flask, request, render_template_string
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

# 定义路径
BASE_DIR = Path(__file__).parent.parent.parent / "data"  # 指向项目根目录下的 data 目录
ORIGINAL_DATA_DIR = BASE_DIR / "original_data"
CLASSIFICATION_DIR = BASE_DIR / "classification"
HISTORY_DIR = CLASSIFICATION_DIR / "history"

app = Flask(__name__)

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>分类管理后台</title>
    <style>
        table { border-collapse: collapse; }
        td, th { border: 1px solid #ddd; padding: 8px; }
        .history { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>属性分类管理</h1>
    
    <form method="post">
    <table>
        <tr><th>属性代码</th><th>属性名称</th><th>当前分类</th><th>新分类</th></tr>
        {% for item in attributes %}
        <tr>
            <td>{{ item.attribute_code }}</td>
            <td>{{ item.attribute_chinese }}</td>
            <td>{{ item.category_name }}</td>
            <td>
                <select name="{{ item.attribute_code }}">
                    {% for cat in categories %}
                    <option value="{{ cat.category_id }}" 
                        {% if cat.category_id == item.category_id %}selected{% endif %}>
                        {{ cat.category_name }}
                    </option>
                    {% endfor %}
                </select>
            </td>
        </tr>
        {% endfor %}
    </table>
    <button type="submit">保存修改</button>
    </form>

    <div class="history">
        <h3>最近变更</h3>
        {{ change_log|safe }}
    </div>
</body>
</html>
"""

def backup_current_version():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    detail_path = CLASSIFICATION_DIR / "attribute_category_detail.csv"
    backup_path = HISTORY_DIR / f"detail_{timestamp}.csv"
    shutil.copy2(detail_path, backup_path)
    return backup_path.name

def log_change(action_type, changed_by="system", backup_file=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "changed_by": changed_by,
        "backup_file": backup_file
    }
    
    log_path = HISTORY_DIR / "changelog.csv"
    pd.DataFrame([log_entry]).to_csv(log_path, mode='a', header=not log_path.exists(), index=False)

@app.route('/', methods=['GET', 'POST'])
def manage_classification():
    # 加载数据
    master = pd.read_csv(CLASSIFICATION_DIR / "attribute_category_master.csv")
    detail = pd.read_csv(CLASSIFICATION_DIR / "attribute_category_detail.csv")
    cross = pd.read_csv(ORIGINAL_DATA_DIR / "cross_attributes.csv")
    
    # 合并数据
    df = cross.merge(detail, on='attribute_code').merge(master, on='category_id')
    
    # 处理修改
    if request.method == 'POST':
        updates = {}
        for code, cat_id in request.form.items():
            updates[code] = int(cat_id)
        
        # 应用修改
        for code, new_cat in updates.items():
            detail.loc[detail['attribute_code'] == code, 'category_id'] = new_cat
        
        # 备份和保存
        backup_file = backup_current_version()
        detail.to_csv(CLASSIFICATION_DIR / "attribute_category_detail.csv", index=False)
        
        # 记录日志
        log_change("manual_edit", changed_by="admin", backup_file=backup_file)
    
    # 加载变更日志
    try:
        change_log = pd.read_csv(HISTORY_DIR / "changelog.csv").tail(5).to_html()
    except FileNotFoundError:
        change_log = "无历史记录"
    
    return render_template_string(ADMIN_HTML,
        attributes=df.to_dict('records'),
        categories=master.to_dict('records'),
        change_log=change_log
    )

if __name__ == "__main__":
    app.run(port=5001)