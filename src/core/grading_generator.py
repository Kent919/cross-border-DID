import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
import shutil

# 定义路径
BASE_DIR = Path(__file__).parent.parent.parent / "data"
GRADING_DIR = BASE_DIR / "grading"
CONFIG_DIR = GRADING_DIR / "config"  # 更新为 grading/config 目录

def load_config():
    """加载分级规则配置文件"""
    with open(CONFIG_DIR / "grading_rules.yaml") as f:
        return yaml.safe_load(f)

def generate_grading():
    """生成初始分级结果"""
    # 确保目录存在
    GRADING_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)
    (GRADING_DIR / "history").mkdir(exist_ok=True)
    
    # 加载数据
    cross_df = pd.read_csv(BASE_DIR / "original_data/cross_attributes.csv")
    detail_df = pd.read_csv(BASE_DIR / "classification/attribute_category_detail.csv")
    rules = load_config()
    
    # 合并数据
    merged = cross_df.merge(detail_df, on="attribute_code")
    
    # 映射敏感级别
    rule_map = {r['category_id']: r['sensitivity_level'] for r in rules['rules']}
    merged['sensitivity_level'] = merged['category_id'].map(rule_map).fillna('RT02')
    
    # 生成结果
    result = merged[[
        'attribute_code', 
        'attribute_chinese',
        'sensitivity_level',
        'category_id'
    ]]
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    result.to_csv(GRADING_DIR / "inital_grading.csv", index=False)
    shutil.copy2(
        GRADING_DIR / "inital_grading.csv",
        GRADING_DIR / "history" / f"grading_{timestamp}.csv"
    )
    
    # 生成报告
    generate_validation_report(result)
    log_grading_change()

def generate_validation_report(df):
    """生成验证报告"""
    stats = {
        "total": len(df),
        "high_risk": len(df[df['sensitivity_level'] == 'RT01']),
        "medium_risk": len(df[df['sensitivity_level'] == 'RT02']),
        "low_risk": len(df[df['sensitivity_level'] == 'RT03'])
    }
    
    report = f"""
    <html><body>
        <h1>分级验证报告 {datetime.now()}</h1>
        <h2>分级统计</h2>
        <ul>
            <li>总属性数: {stats['total']}</li>
            <li>高敏感属性: {stats['high_risk']}</li>
            <li>中敏感属性: {stats['medium_risk']}</li>
            <li>低敏感属性: {stats['low_risk']}</li>
        </ul>
        <h2>异常检测</h2>
        <p>未分类属性: {len(df[df['sensitivity_level'].isna()])}</p>
    </body></html>
    """
    
    with open(GRADING_DIR / "validation_report.html", "w") as f:
        f.write(report)

def log_grading_change():
    """记录变更日志"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "auto_generate",
        "changed_by": "system"
    }
    log_path = GRADING_DIR / "history/changelog.csv"
    pd.DataFrame([log_entry]).to_csv(log_path, mode='a', header=not log_path.exists(), index=False)

if __name__ == "__main__":
    generate_grading()
