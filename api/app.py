# 在api/app.py中
from fastapi import FastAPI
from src.core import classification

app = FastAPI()

@app.post("/classify")
async def classify_data(data: dict):
    result = classification.process_request(data)
    return {"result": result}
