# 在data/examples/generate_sample.py中
import pandas as pd
import numpy as np

def generate_sample():
    np.random.seed(42)
    data = {
        "attribute1": np.random.normal(0.5, 0.1, 1000),
        "attribute2": np.random.beta(2,5,1000),
        "risk_factor": np.random.exponential(0.5,1000)
    }
    pd.DataFrame(data).to_csv("data/examples/sample_data.csv", index=False)
