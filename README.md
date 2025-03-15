# cross-border-DID
Decentralized Cross-border Digital Identity Attribute Correlation Classification and Grading Certification Research
# 跨境数字身份属性分类分级系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于动态熵权法和改进聚类算法的属性分类分级系统，支持跨境数字身份数据的隐私风险评估和保护策略生成。

## 功能特性  
- **生成数据**：模拟跨境数字身份数据，用于测试和验证系统功能。  
- **属性分类**：将属性分为个人身份信息（PII）、财务信息（FI）、健康信息（HI）和通用信息（GI）。  
- **动态权重计算**：基于熵权法计算属性权重。  
- **改进的 K-means 聚类算法**：用于属性分级。  
- **自适应分级阈值调整**：动态调整分级阈值以适应不同数据分布。  
- **可视化结果输出**：提供直观的分类和分级结果展示。

## 快速开始

### 安装  
```bash
git clone https://github.com/Kent919/cross-border-DID.git  
cd cross-border-DID  
pip install -r requirements.txt  
数据生成模块
功能：生成模拟的跨境数字身份数据，用于测试和验证系统功能。
输入：无
输出：data/original_data/cross_attributes.csv
运行方式：python src/core/generator_data.py
系统参数生成
功能：生成系统配置文件，用于管理分类规则和参数。
输入：无
输出：data/sys_config.csv
运行方式：python src/core/config_manager.py
访问方式：
启动管理后台后，访问 http://127.0.0.1:5001。
功能模块：属性分类管理
1. 功能概述
本模块实现了属性分类的动态管理功能，包括：
属性分类：将属性分为个人身份信息（PII）、财务信息（FI）、健康信息（HI）和通用信息（GI）。
敏感度量化：基于风险因子（关联风险、损害潜势、识别风险）计算属性的综合敏感度评分。
分类结果存储：将分类结果存储于知识图谱中，支持动态更新和版本控制。
管理后台：提供 Web 界面，支持人工调整分类和查看变更历史。
2. 主要功能
2.1 属性分类同步 (sync_classification.py)
输入：data/original_data/cross_attributes.csv
输出：
data/classification/attribute_category_master.csv：分类主表
data/classification/attribute_category_detail.csv：分类明细表
data/classification/reports/validation_*.html：验证报告
data/classification/history/detail_*.csv：历史版本
功能：
根据 mapping_rules.yaml 动态映射属性分类。
计算属性的综合敏感度评分。（后续增加）
生成分类结果并存储于知识图谱（后续增加）。
备份历史版本并记录变更日志。
运行方式：python src/core/sync_classification.py
2.2 分类管理后台 (sync_classification_admin_app.py)
功能：
提供 Web 界面，支持人工调整属性分类。
实时查看分类分布和变更历史。
支持保存修改并生成备份。
访问方式：python src/core/sync_classification_admin_app.py
访问 http://127.0.0.1:5001。
3. 日常操作
修改映射规则：编辑 data/classification/config/mapping_rules.yaml。
人工调整分类：通过管理后台调整属性分类。
查看报告：检查 data/classification/reports/ 目录下的验证报告。
恢复历史版本：从 data/classification/history/ 目录中选择备份文件恢复。
变更日志
2024-11-12：新增属性分类管理模块。
2025-03-12：
新增动态映射规则配置文件 (mapping_rules.yaml)。
新增分类管理后台 (sync_classification_admin_app.py)。
新增历史版本备份和变更日志功能。

## 新增功能四：专家分级管理

### 功能特性
- 一键生成初始分级结果
- 基于配置文件的动态分级规则
- 分级结果版本控制
- 自动生成验证报告

### 文件结构
data/
├── grading/
│   ├── config/
│   │   └── grading_rules.yaml         # 分级规则配置
│   ├── inital_grading.csv             # 初始分级结果
│   └── history/
│       ├── grading_20230801.csv       # 历史版本
│       └── changelog.csv              # 变更日志

风险分析模块说明

功能概述

本模块用于对跨境数据属性进行风险分析，基于贝叶斯网络模型计算风险概率、关联强度和条件熵，并将结果保存为 risk_analysis.csv 文件。同时，提供 Flask 管理界面，支持分级生成和风险分析操作。
主要功能

分级生成：
调用grading_generator.py生成初始分级数据 (inital_grading.csv)。
支持重新生成分级数据并覆盖现有数据。
风险分析：
基于贝叶斯网络模型计算风险概率(P_risk)、关联强度(R)和条件熵(H)。（调节risk_parameters和grading_rules）
结果保存到 risk_analysis.csv 文件中。
管理界面：
提供 Web 界面展示当前分级结果和风险分析结果。
支持通过按钮触发分级生成和风险分析操作。

运行步骤

安装依赖：
pip install pgmpy==0.1.26 flask pandas numpy pyyaml scipy
生成初始分级数据：
python src/core/grading_generator.py
启动风险分析服务：
python src/core/sync_risk_analysis_admin_app.py

注意：关联强度R计算：代码里R是按category_id分组对P_risk进行标准化得到的。要是某个category_id组内的P_risk值都相同，那么该组的R就会是0。在初始化阶段，由于系统属性没有在根据不同法律实践去调节，而只量化了一个标准，根据公式ℛ(𝑡) = 𝑓(𝑃risk,其他動態因素)；因此属性中的同一分类的风险值是一样的。
条件熵H计算：条件熵H是基于category_id分组计算的。如果某个category_id组内的sensitivity_level值都相同，那么该组的条件熵就是0。同上，同一组内的风险水平是一样的，因此条件熵也是0. 
这两个值在不同法律体系中，对属性风险看法和判断认识不一致的情况下，R或H就会有差异。

隐私风险量化模块说明
在data/original_data/目录下放置cross_attributes_extended.csv文件（扩展数据）。是用来计算属性熵的特别参数。sensitivity_level_ext是一个0到1之间的数值表示专家评估的修正系数。
运行python app_routes.py
访问 http://127.0.0.1:5001/quantify
量化结果会保存到data/grading/risk_quantification.csv文件中
其中说明：
1.多源熵计算
原始熵 (H_base)：基于原始数据中的sensitivity_level计算。
扩展熵 (H_ext)：基于sensitivity_level_ext的修正系数计算。
综合熵 (H_combined)：通过加权平均结合H_base和H_ext，公式为：
H_combined = 0.7 * H_base + 0.3 * H_ext
2.动态权重分配
权重计算基于熵值(H)、关联风险(R)和损害潜势(P_risk)。

## 模块7：隐私保护措施管理系统
依赖原系统生成的risk_quantification.csv文件
### 启动步骤

python src/core/protection_mapper.py

http://localhost:5002/protection

功能特性如下：

1.动态阈值计算：
初始阈值基于3σ原则自动计算
支持手动调整阈值参数
2.灵活措施配置：
通过复选框选择各等级保护措施
支持自定义措施组合
3.数据持久化：
配置自动保存为YAML文件
结果输出为CSV文件
以下参数可以自己按需要配置：
theta_high: 1.25
theta_mid: 0.85
theta_low: 0.45
measures:
  high:
  - 加密
  - 脫敏
  - 審計
  mid:
  - 加密
  - 匿名化
  low:
  - 訪問控制
