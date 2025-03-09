# src/core/classification.py
def process_request(data: dict) -> str:
    # 示例逻辑：根据数据返回分类结果
    if "risk_factor" in data and data["risk_factor"] > 0.5:
        return "High Risk"
    else:
        return "Low Risk"
