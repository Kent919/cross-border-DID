import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
import shutil

# 定义路径
# 使用 __file__ 的绝对路径来确定项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # 从 src/core 到项目根目录
BASE_DIR = PROJECT_ROOT / "data"
ORIGINAL_DATA_DIR = BASE_DIR / "original_data"
CLASSIFICATION_DIR = BASE_DIR / "classification"
HISTORY_DIR = CLASSIFICATION_DIR / "history"
REPORT_DIR = CLASSIFICATION_DIR / "reports"

def load_mapping_rules():
    with open(CLASSIFICATION_DIR / "config/mapping_rules.yaml") as f:
        return yaml.safe_load(f)

def generate_category_mapping(rules):
    mapping = {}
    for rule in rules['rules']:
        for code in rule['attribute_codes']:
            mapping[code] = rule['category_id']
    return mapping

def backup_current_version():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    detail_path = CLASSIFICATION_DIR / "attribute_category_detail.csv"
    backup_path = HISTORY_DIR / f"detail_{timestamp}.csv"
    shutil.copy2(detail_path, backup_path)
    return backup_path.name

def generate_validation_report(detail_df):
    validation_results = {
        "total_attributes": len(detail_df),
        "unmapped_attributes": len(detail_df[detail_df['category_id'] == 4]),
        "category_distribution": detail_df['category_id'].value_counts().to_dict()
    }
    
    report_html = f"""
    <html><body>
        <h1>分类验证报告 {datetime.now()}</h1>
        <h2>概要统计</h2>
        <ul>
            <li>总属性数: {validation_results['total_attributes']}</li>
            <li>未映射属性数: {validation_results['unmapped_attributes']}</li>
        </ul>
        <h2>分类分布</h2>
        {detail_df['category_id'].value_counts().to_frame().to_html()}
    </body></html>
    """
    
    report_path = REPORT_DIR / f"validation_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    with open(report_path, 'w') as f:
        f.write(report_html)
    return report_path

def log_change(action_type, changed_by="system", backup_file=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "changed_by": changed_by,
        "backup_file": backup_file
    }
    
    log_path = HISTORY_DIR / "changelog.csv"
    pd.DataFrame([log_entry]).to_csv(log_path, mode='a', header=not log_path.exists(), index=False)

def sync_classification():
    # 初始化目录
    for d in [HISTORY_DIR, REPORT_DIR]:
        d.mkdir(parents=True, exist_ok=True)  # 确保父目录存在
    
    # 加载数据
    cross_df = pd.read_csv(ORIGINAL_DATA_DIR / "cross_attributes.csv")
    rules = load_mapping_rules()
    mapping = generate_category_mapping(rules)
    
    # 生成明细数据
    detail_data = []
    for _, row in cross_df.iterrows():
        code = row['attribute_code']
        detail_data.append({
            "attribute_code": code,
            "category_id": mapping.get(code, rules['default_category'])
        })
    
    detail_df = pd.DataFrame(detail_data)
    
    # 备份和保存
    backup_file = backup_current_version()
    detail_df.to_csv(CLASSIFICATION_DIR / "attribute_category_detail.csv", index=False)
    
    # 生成报告
    report_path = generate_validation_report(detail_df)
    
    # 记录日志
    log_change("auto_sync", backup_file=backup_file)
    
    print(f"同步完成！验证报告：{report_path}")

if __name__ == "__main__":
    sync_classification()