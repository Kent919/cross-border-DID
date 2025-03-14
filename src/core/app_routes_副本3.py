from flask import Flask, render_template_string, redirect, url_for
import pandas as pd
import numpy as np
from pathlib import Path
import os
import yaml
from scipy.stats import entropy
import traceback

# 初始化Flask应用
app = Flask(__name__)

# 常量定义
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GRADING_DIR = BASE_DIR / "grading"
CONFIG_DIR = BASE_DIR / "config"
RISK_PARAMS_PATH = CONFIG_DIR / "risk_parameters.yaml"

# ------------------------- 增强模块 -------------------------
class RiskCalculator:
    @staticmethod
    def calculate_relation_strength(risk_df):
        """动态关联强度计算（解决R全0问题）"""
        # 基础归一化
        min_p = risk_df['P_risk'].min()
        max_p = risk_df['P_risk'].max()
        range_p = max_p - min_p if (max_p - min_p) != 0 else 1e-8
        
        # 类别差异因子
        category_weights = risk_df.groupby('category_id')['P_risk'].transform(
            lambda x: x.mean() / risk_df['P_risk'].mean()
        ).fillna(1.0)
        
        # 合成R值并添加随机扰动
        risk_df['R'] = (risk_df['P_risk'] - min_p) / range_p * category_weights
        risk_df['R'] += np.random.uniform(-0.05, 0.05, len(risk_df))  # ±5%扰动
        
        # 限制范围并分组归一化
        risk_df['R'] = risk_df.groupby('category_id')['R'].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-8)
        )
        return risk_df

class EntropyEnhancer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.ext_cross_path = self.data_dir / "original_data/cross_attributes_extended.csv"
    
    def enhance_entropy(self, risk_df):
        """增强条件熵计算（解决H全0问题）"""
        try:
            ext_cross = pd.read_csv(self.ext_cross_path)
            merged = risk_df.merge(
                ext_cross, 
                on="attribute_code", 
                how="left",
                suffixes=('', '_ext')
            )
            
            # 融合敏感度指标
            merged['combined_sensitivity'] = merged.apply(
                lambda x: self._fuse_sensitivity(
                    x['sensitivity_level'],
                    x.get('sensitivity_level_ext', x['sensitivity_level'])
                ),
                axis=1
            )
            
            # 计算增强熵
            entropy_map = self._calculate_enhanced_entropy(merged)
            risk_df['H'] = risk_df['category_id'].map(entropy_map)
            
        except Exception as e:
            print(f"多源熵计算失败，使用基础熵值: {str(e)}")
            risk_df['H'] = risk_df.groupby('category_id')['sensitivity_level'].transform(
                lambda x: entropy(x.value_counts(normalize=True), base=2)
            )
        
        # 添加随机扰动并归一化
        risk_df['H'] = risk_df['H'] * np.random.uniform(0.8, 1.2, len(risk_df))
        h_min, h_max = risk_df['H'].min(), risk_df['H'].max()
        risk_df['H'] = (risk_df['H'] - h_min) / (h_max - h_min + 1e-8)
        return risk_df

    def _fuse_sensitivity(self, base_val, ext_val):
        """融合敏感度指标"""
        if pd.isna(ext_val):
            return base_val
        return (base_val + ext_val) / 2

    def _calculate_enhanced_entropy(self, df):
        """计算增强条件熵"""
        grouped = df.groupby('category_id')['combined_sensitivity'].value_counts(normalize=True)
        return grouped.groupby(level=0).apply(
            lambda x: entropy(x.values, base=2)
        ).to_dict()

class WeightCalculator:
    @staticmethod
    def calculate_weights(normalized_data):
        """修正权重计算（解决负数问题）"""
        X = normalized_data[['v1', 'v2', 'v3']].values
        
        # 极差标准化
        min_vals = X.min(axis=0)
        max_vals = X.max(axis=0)
        ranges = max_vals - min_vals
        ranges[ranges == 0] = 1e-8
        p_ij = (X - min_vals) / ranges
        
        # 熵值计算
        epsilon = 1e-8
        p_ij = np.clip(p_ij, epsilon, 1)
        p_ij = p_ij / p_ij.sum(axis=0, keepdims=True)
        E = -np.sum(p_ij * np.log(p_ij), axis=0) / np.log(len(p_ij))
        
        # 权重修正
        E = np.clip(E, 0, 0.999)  # 关键修复点
        weights = (1 - E) / (1 - E).sum()
        return weights

# ------------------------- 核心逻辑 -------------------------
def load_risk_params():
    """加载风险参数"""
    if not RISK_PARAMS_PATH.exists():
        default_params = {
            'lambda': {'default': 0.5},
            'alpha': {'default': 1.0},
            'beta': {'default': 1.0}
        }
        RISK_PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RISK_PARAMS_PATH, 'w') as f:
            yaml.dump(default_params, f)
    
    with open(RISK_PARAMS_PATH) as f:
        return yaml.safe_load(f)

def calculate_risk(row, params):
    """风险概率计算"""
    lambda_i = params['lambda'].get(row['attribute_code'], 0.5)
    alpha_ij = params['alpha'].get(row['category_id'], 1.0)
    beta_ij = params['beta'].get(f"{row['attribute_code']}_{row['category_id']}", 1.0)
    return row['P_risk'] * lambda_i * alpha_ij * beta_ij

# ------------------------- Flask路由 -------------------------
@app.route('/quantify')
def quantify_risk():
    """执行量化计算"""
    try:
        # 加载数据
        risk_df = pd.read_csv(GRADING_DIR / "risk_analysis.csv")
        params = load_risk_params()
        
        # 动态计算指标
        risk_df = RiskCalculator.calculate_relation_strength(risk_df)
        risk_df = EntropyEnhancer(BASE_DIR).enhance_entropy(risk_df)
        
        # 标准化指标
        risk_df['v1'] = risk_df['R']
        risk_df['v2'] = risk_df['P_risk'] / risk_df['P_risk'].max()
        risk_df['v3'] = 1 - risk_df['H']
        
        # 计算权重
        weights = WeightCalculator.calculate_weights(risk_df)
        
        # 综合评分
        risk_df['L'] = (risk_df[['v1', 'v2', 'v3']] * weights).sum(axis=1)
        risk_df.to_csv(GRADING_DIR / "risk_quantification.csv", index=False)
        
        return render_template_string(QUANT_TEMPLATE, 
                                   data=risk_df.to_dict('records'),
                                   weights=weights.tolist())
    
    except Exception as e:
        return f"量化失败: {str(e)}", 500

# ------------------------- 前端模板 -------------------------
QUANT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>隐私风险量化</title>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f0f8ff; }
    </style>
</head>
<body>
    <h1>量化结果</h1>
    <div>
        <h3>权重分配</h3>
        <ul>
            <li>关联风险权重: {{ "%.1f"|format(weights[0]*100) }}%</li>
            <li>损害潜势权重: {{ "%.1f"|format(weights[1]*100) }}%</li>
            <li>识别风险权重: {{ "%.1f"|format(weights[2]*100) }}%</li>
        </ul>
    </div>
    <table>
        <tr>
            <th>属性代码</th><th>属性名称</th><th>R</th><th>H</th><th>L</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.attribute_code }}</td>
            <td>{{ item.attribute_chinese }}</td>
            <td>{{ "%.3f"|format(item.R) }}</td>
            <td>{{ "%.3f"|format(item.H) }}</td>
            <td>{{ "%.3f"|format(item.L) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# ------------------------- 主程序 -------------------------
if __name__ == "__main__":
    # 初始化目录
    GRADING_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "original_data").mkdir(parents=True, exist_ok=True)
    
    # 启动应用
    app.run(port=5001, debug=True, use_reloader=False)