# File: src/core/app_routes.py
from flask import Flask, render_template_string, redirect, url_for
import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from scipy.stats import entropy

# 初始化 Flask 应用
app = Flask(__name__)

# 常量定义
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GRADING_DIR = BASE_DIR / "grading"
CONFIG_DIR = BASE_DIR / "config"
RISK_PARAMS_PATH = CONFIG_DIR / "risk_parameters.yaml"

# ------------------------- 动态调节模块 -------------------------
class RiskAdjuster:
    @staticmethod
    def adjust_relation_strength(risk_df, params):
        """动态调整关联强度"""
        jurisdiction_weights = params.get('jurisdiction_weights', {})
        default_weight = params.get('default_jurisdiction_weight', 0.1)
        
        risk_df['R_dynamic'] = risk_df.apply(
            lambda row: max(
                row['R'] * (1 + jurisdiction_weights.get(row['category_id'], default_weight)),
                params.get('min_R', 0.05)
            ),
            axis=1
        )
        return risk_df

    @staticmethod
    def normalize_indicators(risk_df):
        """标准化风险指标"""
        R_min, R_max = risk_df['R_dynamic'].min(), risk_df['R_dynamic'].max()
        P_max = max(risk_df['P_risk'].max(), 1e-8)
        H_max = max(risk_df['H_adjusted'].max(), 1e-8)
        
        risk_df['v1'] = (risk_df['R_dynamic'] - R_min) / ((R_max - R_min) or 1)
        risk_df['v2'] = risk_df['P_risk'] / P_max
        risk_df['v3'] = 1 - (risk_df['H_adjusted'] / H_max)
        return risk_df

# ------------------------- 多源条件熵模块 -------------------------
class EntropyEnhancer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.ext_cross_path = self.data_dir / "original_data/cross_attributes_extended.csv"
    
    def enhance_entropy(self, risk_df):
        """多源增强条件熵计算"""
        try:
            ext_cross = pd.read_csv(self.ext_cross_path)
            merged = risk_df.merge(
                ext_cross, 
                on="attribute_code", 
                how="left",
                suffixes=('', '_ext')
            )
            merged['combined_sensitivity'] = merged.apply(
                lambda x: np.nanmean([x['sensitivity_level'], x.get('sensitivity_level_ext')]),
                axis=1
            )
            entropy_map = self._calculate_entropy(merged)
            risk_df['H_adjusted'] = risk_df['category_id'].map(entropy_map)
        except Exception as e:
            print(f"多源熵计算失败，使用原始值: {str(e)}")
            risk_df['H_adjusted'] = risk_df['H']
        risk_df['H_adjusted'] = risk_df['H_adjusted'].clip(lower=0.01)
        return risk_df
    
    def _calculate_entropy(self, df):
        """计算条件熵"""
        grouped = df.groupby('category_id')['combined_sensitivity'].value_counts(normalize=True)
        return grouped.groupby(level=0).apply(lambda x: entropy(x.values, base=2)).to_dict()

# ------------------------- 隐私风险量化模块 -------------------------
class PrivacyRiskQuantifier:
    def __init__(self, config_path, data_dir):
        self.config_path = config_path
        self.enhancer = EntropyEnhancer(data_dir)
    
    def _load_params(self):
        """加载或生成默认参数"""
        if not self.config_path.exists():
            print("配置文件不存在，生成默认配置...")
            default_params = {
                'jurisdiction_weights': {'default': 0.1},
                'min_R': 0.05,
                'min_H': 0.01
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(default_params, f)
        
        with open(self.config_path) as f:
            params = yaml.safe_load(f)
        
        # 参数校验
        required_keys = ['jurisdiction_weights', 'min_R', 'min_H']
        for key in required_keys:
            if key not in params:
                raise ValueError(f"配置文件中缺失必要参数: {key}")
        
        return params
    
    def _calculate_weights(self, normalized_data):
        """动态熵权法计算"""
        X = normalized_data[['v1', 'v2', 'v3']].values
        min_vals, max_vals = X.min(axis=0), X.max(axis=0)
        ranges = max_vals - min_vals
        ranges[ranges == 0] = 1e-8
        p_ij = (X - min_vals) / ranges
        epsilon = 1e-8
        p_ij = np.clip(p_ij, epsilon, 1)
        E = -np.sum(p_ij * np.log(p_ij), axis=0) / np.log(len(p_ij))
        weights = (1 - E) / (1 - E).sum()
        return weights
    
    def quantify(self, input_path, output_path):
        """执行完整量化流程"""
        risk_df = pd.read_csv(input_path)
        params = self._load_params()
        
        # 动态调节流程
        risk_df = RiskAdjuster.adjust_relation_strength(risk_df, params)
        risk_df = self.enhancer.enhance_entropy(risk_df)
        risk_df = RiskAdjuster.normalize_indicators(risk_df)
        
        # 权重计算
        weights = self._calculate_weights(risk_df)
        
        # 综合评分
        risk_df['L'] = (risk_df[['v1', 'v2', 'v3']] * weights).sum(axis=1)
        risk_df.to_csv(output_path, index=False)
        return risk_df, weights

# ------------------------- 路由定义 -------------------------
@app.route('/')
def index():
    """首页重定向到分级管理"""
    return redirect(url_for('grading_management'))

@app.route('/test')
def test():
    """测试路由"""
    return "Hello, Flask!"

@app.route('/grading')
def grading_management():
    """分级管理主界面"""
    try:
        # 加载分级数据
        grading_df = pd.read_csv(GRADING_DIR / "inital_grading.csv")
        # 加载验证报告
        report_content = open(GRADING_DIR / "validation_report.html").read()
        # 加载风险分析数据
        risk_df = pd.read_csv(GRADING_DIR / "risk_analysis.csv") if os.path.exists(GRADING_DIR / "risk_analysis.csv") else pd.DataFrame()
    except Exception as e:
        print(f"界面加载错误: {str(e)}")
        # 如果加载失败，使用空数据
        grading_df = pd.DataFrame(columns=["attribute_code", "attribute_chinese", "sensitivity_level"])
        report_content = "<p>数据加载失败，请检查后台日志</p>"
        risk_df = pd.DataFrame()

    return render_template_string(
        GRADING_HTML,
        data=grading_df.to_dict('records'),
        report=report_content,
        risk_data=risk_df.to_dict('records')
    )

@app.route('/quantify')
def run_quantification():
    """执行隐私风险量化"""
    try:
        # 初始化量化器
        quantifier = PrivacyRiskQuantifier(
            config_path=RISK_PARAMS_PATH,
            data_dir=BASE_DIR
        )
        
        # 执行量化
        result_df, weights = quantifier.quantify(
            input_path=GRADING_DIR / "risk_analysis.csv",
            output_path=GRADING_DIR / "risk_quantification.csv"
        )
        
        # 返回量化结果页面
        return render_template_string(
            QUANT_TEMPLATE,
            data=result_df.to_dict('records'),
            weights=[round(w, 4) for w in weights]
        )
    except FileNotFoundError as e:
        return f"配置文件缺失: {str(e)}", 500
    except ValueError as e:
        return f"参数配置错误: {str(e)}", 500
    except Exception as e:
        return f"未知错误: {str(e)}", 500

# ------------------------- 前端模板 -------------------------
GRADING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>跨境数据分级管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f7fa; }
    </style>
</head>
<body>
    <h1>跨境数据属性分级管理</h1>
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
</body>
</html>
"""

QUANT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>隐私风险量化结果</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f7fa; }
        .weight-panel { margin: 1rem 0; padding: 1rem; background: #f8f9fc; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>隐私风险量化结果</h1>
    
    <div class="weight-panel">
        <h3>动态权重分配</h3>
        <ul>
            <li>关联风险权重: {{ "%.1f"|format(weights[0]*100) }}%</li>
            <li>损害潜势权重: {{ "%.1f"|format(weights[1]*100) }}%</li>
            <li>识别风险权重: {{ "%.1f"|format(weights[2]*100) }}%</li>
        </ul>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>属性代码</th>
                <th>属性名称</th>
                <th>关联风险</th>
                <th>损害潜势</th>
                <th>识别风险</th>
                <th>综合评分</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data %}
            <tr>
                <td>{{ item.attribute_code }}</td>
                <td>{{ item.attribute_chinese }}</td>
                <td>{{ "%.3f"|format(item.v1) }}</td>
                <td>{{ "%.3f"|format(item.v2) }}</td>
                <td>{{ "%.3f"|format(item.v3) }}</td>
                <td>{{ "%.3f"|format(item.L) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

# ------------------------- 主程序入口 -------------------------
if __name__ == "__main__":
    # 确保数据目录存在
    GRADING_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 运行应用
    app.run(port=5001, debug=True)