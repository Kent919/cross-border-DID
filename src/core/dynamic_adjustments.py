import pandas as pd
import numpy as np

class RiskAdjuster:
    @staticmethod
    def adjust_relation_strength(risk_df, params):
        # 动态调整关联强度（公式3.5增强）
        jurisdiction_weights = params.get('jurisdiction_weights', {})
        default_weight = params.get('default_jurisdiction_weight', 0.1)
        
        risk_df['R_dynamic'] = risk_df.apply(
            lambda row: max(
                row['R'] * (1 + jurisdiction_weights.get(row['category_id'], default_weight),
                params.get('min_R', 0.05)
            ),
            axis=1
        )
        return risk_df

    @staticmethod
    def normalize_indicators(risk_df):
        # 标准化处理（公式3.5-3.7）
        R_min, R_max = risk_df['R_dynamic'].min(), risk_df['R_dynamic'].max()
        P_max = max(risk_df['P_risk'].max(), 1e-8)
        H_max = max(risk_df['H_adjusted'].max(), 1e-8)
        
        risk_df['v1'] = (risk_df['R_dynamic'] - R_min) / ((R_max - R_min) or 1)
        risk_df['v2'] = risk_df['P_risk'] / P_max
        risk_df['v3'] = 1 - (risk_df['H_adjusted'] / H_max)
        return risk_df
