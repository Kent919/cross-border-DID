# cross-border-DID
Decentralized Cross-border Digital Identity Attribute Correlation Classification and Grading Certification Research
# 跨境数字身份属性分类分级系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于动态熵权法和改进聚类算法的属性分类分级系统，支持跨境数字身份数据的隐私风险评估和保护策略生成。

## 功能特性
- 生成数据
- 动态权重计算（熵权法）
- 改进的K-means聚类算法
- 自适应分级阈值调整
- 可视化结果输出

## 快速开始

### 安装
```bash
git clone https://github.com/Kent919/cross-border-DID.git
pip install -r requirements.txt
## REST API 接口

#本项目提供了一个 REST API 接口，用于分类数据。接口定义在 `api/app.py` 中。

### 启动 API 服务器
#```bash
uvicorn api.app:app --reload