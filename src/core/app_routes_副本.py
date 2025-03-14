# File: app_routes.py
from flask import Blueprint, render_template_string, redirect, url_for
import pandas as pd
import yaml
import numpy as np
from pathlib import Path
from scipy.stats import entropy

# 初始化蓝图
quant_bp = Blueprint('quant', __name__, url_prefix='/quant')

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

# ------------------------- 主量化逻辑 -------------------------
class PrivacyRiskQuantifier:
    def __init__(self, config_path, data_dir):
        self.config_path = config_path
        self.enhancer = EntropyEnhancer(data_dir)
    
    def _load_params(self):
        """加载动态参数"""
        with open(self.config_path) as f:
            params = yaml.safe_load(f)
        assert 'jurisdiction_weights' in params, "缺失必要参数: jurisdiction_weights"
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
@quant_bp.route('/quantify')
def run_quantification():
    """执行隐私风险量化"""
    try:
        quantifier = PrivacyRiskQuantifier(
            config_path=RISK_PARAMS_PATH,
            data_dir=BASE_DIR
        )
        result_df, weights = quantifier.quantify(
            input_path=GRADING_DIR / "risk_analysis.csv",
            output_path=GRADING_DIR / "risk_quantification.csv"
        )
        return render_template_string(
            QUANT_TEMPLATE,
            data=result_df.to_dict('records'),
            weights=[round(w, 4) for w in weights]
        )
    except Exception as e:
        return f"量化失败: {str(e)}", 500

# ------------------------- 前端模板 -------------------------
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
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(quant_bp)
    app.run(port=5001, debug=True)
