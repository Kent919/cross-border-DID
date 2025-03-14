from flask import Flask, request, render_template_string, redirect, url_for
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import os

# 定义路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GRADING_DIR = BASE_DIR / "grading"
CONFIG_DIR = GRADING_DIR / "config"

# 初始化 Flask 应用
app = Flask(__name__)

# 根路由：重定向到分级管理页面
@app.route('/')
def index():
    return redirect(url_for('grading_management'))

# 分级管理页面
@app.route('/grading')
def grading_management():
    # 加载分级数据
    try:
        grading_df = pd.read_csv(GRADING_DIR / "inital_grading.csv")
    except FileNotFoundError:
        grading_df = pd.DataFrame(columns=["attribute_code", "attribute_chinese", "sensitivity_level"])
    
    return render_template_string(GRADING_HTML, data=grading_df.to_dict('records'))

# 分级生成接口
@app.route('/generate_grading')
def trigger_grading():
    try:
        # 动态构建 grading_generator.py 的路径
        grading_generator_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),  # 当前文件所在目录
            "../src/core/grading_generator.py"          # 相对路径
        )
        # 确保路径正确
        if not os.path.exists(grading_generator_path):
            raise FileNotFoundError(f"File not found: {grading_generator_path}")
        
        # 调用 grading_generator.py
        subprocess.run(["python", grading_generator_path], check=True)
        return redirect(url_for('grading_management'))
    except subprocess.CalledProcessError as e:
        return f"Error generating grading: {e}", 500
    except FileNotFoundError as e:
        return f"File not found: {e}", 500

# 分级管理页面模板
GRADING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>专家分级管理</title>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        button { margin-bottom: 20px; padding: 10px 20px; font-size: 16px; }
    </style>
</head>
<body>
    <h1>专家分级管理</h1>
    <button onclick="generateGrading()">生成初始分级</button>
    <table>
        <tr>
            <th>属性代码</th>
            <th>属性名称</th>
            <th>敏感级别</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.attribute_code }}</td>
            <td>{{ item.attribute_chinese }}</td>
            <td>{{ item.sensitivity_level }}</td>
        </tr>
        {% endfor %}
    </table>
    <script>
    function generateGrading() {
        fetch('/generate_grading')
        .then(response => {
            if (response.ok) {
                alert('分级已生成，页面即将刷新');
                window.location.reload();
            } else {
                alert('分级生成失败');
            }
        })
        .catch(err => console.error(err));
    }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # 确保目录存在
    GRADING_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (GRADING_DIR / "history").mkdir(parents=True, exist_ok=True)
    
    # 启动 Flask 应用
    app.run(port=5001, debug=True)