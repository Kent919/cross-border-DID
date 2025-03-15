# src/core/protection_mapper.py
from flask import Flask, render_template_string, request, redirect, url_for
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import traceback

# 初始化Flask应用
app = Flask(__name__)

# *************** 路径配置 ***************
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # 项目根目录
DATA_DIR = BASE_DIR / "data"
GRADING_DIR = DATA_DIR / "grading"
CONFIG_DIR = DATA_DIR / "config"

# 输入输出文件路径
RISK_QUANTIFICATION_PATH = GRADING_DIR / "risk_quantification.csv"
PROTECTION_MEASURES_PATH = GRADING_DIR / "protection_measures.csv"
THRESHOLD_PARAMS_PATH = CONFIG_DIR / "protection_thresholds.yaml"

# *************** 核心逻辑类 ***************
class ProtectionEngine:
    @staticmethod
    def load_risk_data():
        """加载风险量化数据"""
        return pd.read_csv(RISK_QUANTIFICATION_PATH)

    @staticmethod
    def calculate_thresholds(df):
        """动态计算分级阈值（公式3.18）"""
        l_values = df['L']
        mu = round(l_values.mean(), 3)
        sigma = round(l_values.std(), 3)
        
        return {
            'theta_high': mu + 2 * sigma,
            'theta_mid': (mu + (mu - sigma)) / 2,  # 自定义中间值计算
            'theta_low': mu - sigma,
            'measures': {
                'high': ['加密', '脫敏', '審計'],
                'mid': ['加密', '匿名化'],
                'low': ['訪問控制']
            }
        }

    @staticmethod
    def map_protection(df, params):
        """映射保护措施"""
        conditions = [
            df['L'] >= params['theta_high'],
            (df['L'] >= params['theta_low']) & (df['L'] < params['theta_high']),
            df['L'] < params['theta_low']
        ]
        choices = [
            '|'.join(params['measures']['high']),
            '|'.join(params['measures']['mid']),
            '|'.join(params['measures']['low'])
        ]
        df['protection_measures'] = np.select(conditions, choices, default='未定義')
        return df

# *************** 路由处理 ***************
@app.route('/protection', methods=['GET', 'POST'])
def protection_management():
    try:
        # 加载或初始化配置
        try:
            with open(THRESHOLD_PARAMS_PATH) as f:
                params = yaml.safe_load(f) or {}
        except FileNotFoundError:
            params = {}

        # 处理表单提交
        if request.method == 'POST':
            # 解析表单数据
            new_params = {
                'theta_high': float(request.form['theta_high']),
                'theta_mid': float(request.form['theta_mid']),
                'theta_low': float(request.form['theta_low']),
                'measures': {
                    'high': request.form.getlist('measures_high'),
                    'mid': request.form.getlist('measures_mid'),
                    'low': request.form.getlist('measures_low')
                }
            }
            
            # 保存配置
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(THRESHOLD_PARAMS_PATH, 'w') as f:
                yaml.dump(new_params, f, allow_unicode=True)
            
            return redirect(url_for('protection_management'))

        # 加载风险数据
        df = ProtectionEngine.load_risk_data()
        
        # 自动生成初始配置
        if not params:
            params = ProtectionEngine.calculate_thresholds(df)
        
        # 映射保护措施
        result_df = ProtectionEngine.map_protection(df.copy(), params)
        
        # 保存结果
        GRADING_DIR.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(PROTECTION_MEASURES_PATH, index=False)
        
        return render_template_string(PROTECTION_TEMPLATE, 
                                    params=params,
                                    data=result_df.to_dict('records'))

    except Exception as e:
        traceback.print_exc()
        return f"操作失败: {str(e)}", 500

# *************** 前端模板 ***************
PROTECTION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>隐私保护措施管理系统</title>
    <style>
        .config-panel {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px auto;
            width: 70%;
        }
        table {
            width: 90%;
            margin: 20px auto;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th { background-color: #e9ecef; }
        input[type="number"] {
            width: 120px;
            padding: 5px;
            margin: 5px;
        }
        .measures-group {
            margin: 15px 0;
            padding: 10px;
            background: #fff;
            border-radius: 4px;
        }
        .submit-btn {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1 style="text-align: center; color: #2c3e50;">隐私保护分级配置</h1>
    
    <div class="config-panel">
        <form method="POST">
            <h3>⚙️ 阈值配置</h3>
            <div>
                <label>高敏感阈值 (θ_high):</label>
                <input type="number" step="0.001" name="theta_high" 
                       value="{{ params.get('theta_high', 1.0) }}" required>
                
                <label>中间阈值 (θ_mid):</label>
                <input type="number" step="0.001" name="theta_mid" 
                       value="{{ params.get('theta_mid', 0.7) }}" required>
                
                <label>低敏感阈值 (θ_low):</label>
                <input type="number" step="0.001" name="theta_low" 
                       value="{{ params.get('theta_low', 0.3) }}" required>
            </div>

            <h3>🛡️ 保护措施配置</h3>
            <div class="measures-group">
                <strong>高级保护措施 (L ≥ θ_high):</strong><br>
                <label><input type="checkbox" name="measures_high" value="加密" 
                    {{ 'checked' if '加密' in params.get('measures', {}).get('high', []) }}> 加密</label>
                <label><input type="checkbox" name="measures_high" value="脫敏" 
                    {{ 'checked' if '脫敏' in params.measures.get('high', []) }}> 脫敏</label>
                <label><input type="checkbox" name="measures_high" value="審計" 
                    {{ 'checked' if '審計' in params.measures.get('high', []) }}> 審計</label>
            </div>

            <div class="measures-group">
                <strong>中级保护措施 (θ_low ≤ L < θ_high):</strong><br>
                <label><input type="checkbox" name="measures_mid" value="加密" 
                    {{ 'checked' if '加密' in params.measures.get('mid', []) }}> 加密</label>
                <label><input type="checkbox" name="measures_mid" value="匿名化" 
                    {{ 'checked' if '匿名化' in params.measures.get('mid', []) }}> 匿名化</label>
            </div>

            <div class="measures-group">
                <strong>基础保护措施 (L < θ_low):</strong><br>
                <label><input type="checkbox" name="measures_low" value="訪問控制" 
                    {{ 'checked' if '訪問控制' in params.measures.get('low', []) }}> 訪問控制</label>
            </div>

            <div style="text-align: center; margin-top: 20px;">
                <input type="submit" value="💾 保存配置" class="submit-btn">
            </div>
        </form>
    </div>

    <table>
        <tr>
            <th>属性代码</th>
            <th>属性名称</th>
            <th>敏感级别</th>
            <th>综合评分(L)</th>
            <th>保护措施</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.attribute_code }}</td>
            <td>{{ item.attribute_chinese }}</td>
            <td>{{ item.sensitivity_level }}</td>
            <td>{{ "%.3f"|format(item.L) }}</td>
            <td>{{ item.protection_measures }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

if __name__ == "__main__":
    # 创建必要目录
    GRADING_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 启动应用（使用独立端口）
    app.run(port=5002, debug=True)
