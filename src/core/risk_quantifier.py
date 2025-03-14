import yaml
import numpy as np
from .dynamic_adjustments import RiskAdjuster
from .entropy_calculation import EntropyEnhancer

class PrivacyRiskQuantifier:
    def __init__(self, config_path, data_dir):
        self.config_path = config_path
        self.enhancer = EntropyEnhancer(data_dir)
    
    def _load_params(self):
        with open(self.config_path) as f:
            params = yaml.safe_load(f)
        # 参数校验
        assert 'jurisdiction_weights' in params, "缺失必要参数: jurisdiction_weights"
        return params
    
    def _calculate_weights(self, normalized_data):
        X = normalized_data[['v1', 'v2', 'v3']].values
        # 极差标准化（公式3.9）
        min_vals, max_vals = X.min(axis=0), X.max(axis=0)
        ranges = max_vals - min_vals
        ranges[ranges == 0] = 1e-8
        p_ij = (X - min_vals) / ranges
        # 熵权计算（公式3.8）
        epsilon = 1e-8
        p_ij = np.clip(p_ij, epsilon, 1)
        E = -np.sum(p_ij * np.log(p_ij), axis=0) / np.log(len(p_ij))
        weights = (1 - E) / (1 - E).sum()
        return weights
    
    def quantify(self, input_path, output_path):
        # 数据加载
        risk_df = pd.read_csv(input_path)
        params = self._load_params()
        
        # 动态调节流程
        risk_df = RiskAdjuster.adjust_relation_strength(risk_df, params)
        risk_df = self.enhancer.enhance_entropy(risk_df)
        risk_df = RiskAdjuster.normalize_indicators(risk_df)
        
        # 权重计算
        weights = self._calculate_weights(risk_df)
        
        # 综合评分（公式3.4）
        risk_df['L'] = (risk_df[['v1', 'v2', 'v3']] * weights).sum(axis=1)
        risk_df.to_csv(output_path, index=False)
        return risk_df, weights
