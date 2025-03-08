from src.core import classification, clustering
from src.utils import data_processor, visualization
import pandas as pd

def run_pipeline(input_path, output_path):
    # 数据加载
    df = pd.read_csv(input_path)
    
    # 预处理
    processed_df = data_processor.normalize_risk_factors(df)
    
    # 分类分级
    model = clustering.RiskAdjustedKMeans()
    results = classification.classify_data(processed_df, model)
    
    # 结果保存
    results.to_csv(output_path, index=False)
    
    # 生成可视化
    visualization.plot_results(results)
    
if __name__ == "__main__":
    run_pipeline("data/input.csv", "output/results.csv")
