import csv
import os

# 数据存储路径
DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "sys_config.csv")

# 定义参数列表
PARAMETERS = [
    {
        "param_id": "lambda_i_id",
        "type": "系数",
        "func_name": "公式3.4",
        "func_value": 1.0,
        "param_desc": "单属性识别系数，衡量属性单独泄露时的识别能力，如身份证号的lambda_i = 1.0（直接识别）"
    },
    {
        "param_id": "alpha_ij_id",
        "type": "系数",
        "func_name": "公式3.4",
        "func_value": 1.2,
        "param_desc": "跨境场景下的司法管辖权加权因子，反映不同法律框架对属性敏感性的影响，如GDPR下生物特征数据的alpha_ij = 1.2"
    },
    {
        "param_id": "beta_ij_id",
        "type": "系数",
        "func_name": "公式3.4",
        "func_value": 1.5,
        "param_desc": "属性在场景下的风险影响因子，衡量特定场景中属性关联的放大效应，如医疗场景中基因数据与病历信息的beta_ij = 1.5"
    },
    {
        "param_id": "theta_high_id",
        "type": "评级参数",
        "func_name": "风险评级",
        "func_value": 0.8,
        "param_desc": "高风险评级阈值"
    },
    {
        "param_id": "theta_mid_id",
        "type": "评级参数",
        "func_name": "风险评级",
        "func_value": 0.5,
        "param_desc": "中风险评级阈值"
    },
    {
        "param_id": "theta_low_id",
        "type": "评级参数",
        "func_name": "风险评级",
        "func_value": 0.2,
        "param_desc": "低风险评级阈值"
    },
    {
        "param_id": "encryption_id",
        "type": "隐私保护措施",
        "func_name": "数据安全",
        "func_value": 1,
        "param_desc": "数据加密措施，启用为1，禁用为0"
    },
    {
        "param_id": "access_control_id",
        "type": "隐私保护措施",
        "func_name": "数据安全",
        "func_value": 1,
        "param_desc": "访问控制措施，启用为1，禁用为0"
    },
    {
        "param_id": "data_masking_id",
        "type": "隐私保护措施",
        "func_name": "数据安全",
        "func_value": 1,
        "param_desc": "数据脱敏措施，启用为1，禁用为0"
    },
    {
        "param_id": "anonymization_id",
        "type": "隐私保护措施",
        "func_name": "数据安全",
        "func_value": 1,
        "param_desc": "匿名处理措施，启用为1，禁用为0"
    },
    {
        "param_id": "audit_monitoring_id",
        "type": "隐私保护措施",
        "func_name": "数据安全",
        "func_value": 1,
        "param_desc": "审计监控措施，启用为1，禁用为0"
    }
]

def create_config_file():
    """
    创建参数配置文件
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(CONFIG_FILE, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["param_id", "type", "func_name", "func_value", "param_desc"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for param in PARAMETERS:
            writer.writerow(param)

def read_config_file():
    """
    读取参数配置文件
    """
    if not os.path.exists(CONFIG_FILE):
        create_config_file()
    params = []
    with open(CONFIG_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            params.append(row)
    return params

def save_config_file(params):
    """
    保存参数配置文件
    """
    with open(CONFIG_FILE, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["param_id", "type", "func_name", "func_value", "param_desc"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for param in params:
            writer.writerow(param)
