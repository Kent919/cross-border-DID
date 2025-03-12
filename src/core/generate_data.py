import csv
import os

# 预设的身份属性数据
attributes = [
    ("A001", "姓名", "Name"),
    ("A002", "性别", "Gender"),
    ("A003", "出生日期", "Date of Birth"),
    # 可根据需要添加更多属性
]

def generate_data():
    data_path = "data/original_data/cross_attributes.csv"
    # 检查数据文件是否已存在
    if os.path.exists(data_path):
        return "数据已生成"
    else:
        # 创建存储目录
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        # 生成数据并保存为 CSV 文件
        with open(data_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["attribute_code", "attribute_chinese", "attribute_english"])
            for attr in attributes:
                writer.writerow(attr)
        return "正在生成数据，请稍候..."

if __name__ == "__main__":
    result = generate_data()
    print(result)
