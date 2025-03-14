# src/core/sync_grading_admin_app.py
from flask import Flask, request, render_template_string, redirect, url_for
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import os

# 定义与grading_generator.py一致的路径体系
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GRADING_DIR = BASE_DIR / "grading"
CONFIG_DIR = GRADING_DIR / "config"

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('grading_management'))

@app.route('/grading')
def grading_management():
    """分级管理主界面"""
    try:
        # 加载最新分级数据
        grading_df = pd.read_csv(GRADING_DIR / "inital_grading.csv")
        report_content = open(GRADING_DIR / "validation_report.html").read()
    except FileNotFoundError:
        grading_df = pd.DataFrame(columns=["attribute_code", "attribute_chinese", "sensitivity_level"])
        report_content = "<p>暂无验证报告</p>"
    
    return render_template_string(
        GRADING_HTML,
        data=grading_df.to_dict('records'),
        report=report_content
    )

@app.route('/generate_grading')
def trigger_grading():
    """触发分级生成"""
    try:
        # 获取当前脚本所在目录（src/core）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        generator_path = os.path.join(current_dir, "grading_generator.py")
        
        # 验证生成器存在
        if not os.path.exists(generator_path):
            raise RuntimeError(f"Generator script not found at: {generator_path}")
        
        # 执行生成脚本
        result = subprocess.run(
            ["python", generator_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 检查执行结果
        if result.returncode != 0:
            raise RuntimeError(f"Generator failed: {result.stderr}")
            
        return redirect(url_for('grading_management'))
    
    except Exception as e:
        error_msg = f"生成失败: {str(e)}"
        return render_template_string(ERROR_HTML, error=error_msg), 500

# 页面模板
GRADING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>跨境数据分级管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        .container { display: grid; grid-template-columns: 3fr 2fr; gap: 2rem; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f5f7fa; }
        .report-box { background: #f8f9fc; padding: 1.5rem; border-radius: 8px; }
        button { 
            background: #4CAF50; 
            color: white; 
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 2rem;
        }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
    <h1>跨境数据属性分级管理</h1>
    <button onclick="generateGrading()">重新生成分级</button>
    
    <div class="container">
        <div>
            <h2>当前分级结果</h2>
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
        </div>
        
        <div class="report-box">
            <h2>验证报告</h2>
            {{ report|safe }}
        </div>
    </div>

    <script>
    function generateGrading() {
        if(confirm('确认要重新生成分级吗？这将会覆盖现有数据！')) {
            fetch('/generate_grading')
            .then(response => {
                if (response.ok) {
                    alert('分级生成成功，页面即将刷新');
                    window.location.reload();
                } else {
                    response.text().then(t => alert(t));
                }
            })
            .catch(err => alert('网络错误: ' + err));
        }
    }
    </script>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h1>操作失败</h1>
    <p style="color: red;">{{ error }}</p>
    <button onclick="window.history.back()">返回</button>
</body>
</html>
"""

if __name__ == "__main__":
    # 初始化目录结构
    GRADING_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (GRADING_DIR / "history").mkdir(parents=True, exist_ok=True)
    
    # 启动应用
    app.run(port=5001, debug=True)