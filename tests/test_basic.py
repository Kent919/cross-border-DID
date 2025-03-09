# tests/test_example.py
import pytest
from src.core.classification import process_request

def test_classification():
    data = {"risk_factor": 0.7}
    result = process_request(data)
    assert result == "High Risk"
