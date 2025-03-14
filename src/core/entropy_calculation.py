from pathlib import Path
import pandas as pd
from scipy.stats import entropy

class EntropyEnhancer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.ext_cross_path = self.data_dir / "original_data/cross_attributes_extended.csv"
    
    def enhance_entropy(self, risk_df):
        try:
            ext_cross = pd.read_csv(self.ext_cross_path)
            merged = risk_df.merge(
                ext_cross, 
                on="attribute_code", 
                how="left",
                suffixes=('', '_ext')
            )
            # 融合多源敏感性数据
            merged['combined_sensitivity'] = merged.apply(
                lambda x: np.nanmean([x['sensitivity_level'], x.get('sensitivity_level_ext')]),
                axis=1
            )
            # 重新计算条件熵
            entropy_map = self._calculate_entropy(merged)
            risk_df['H_adjusted'] = risk_df['category_id'].map(entropy_map)
        except Exception as e:
            print(f"多源熵计算失败，使用原始值: {str(e)}")
            risk_df['H_adjusted'] = risk_df['H']
        # 防零值处理
        risk_df['H_adjusted'] = risk_df['H_adjusted'].clip(lower=0.01)
        return risk_df
    
    def _calculate_entropy(self, df):
        grouped = df.groupby('category_id')['combined_sensitivity'].value_counts(normalize=True)
        return grouped.groupby(level=0).apply(lambda x: entropy(x.values, base=2)).to_dict()
