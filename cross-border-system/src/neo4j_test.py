from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取配置
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
print(os.getenv("NEO4J_URI"))
print(os.getenv("NEO4J_USER"))
print(os.getenv("NEO4J_PASSWORD"))

try:
    # 创建驱动
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # 测试连接
    with driver.session() as session:
        result = session.run("RETURN 1")
        print("✅ 连接成功，测试结果：", result.single()[0])
except Exception as e:
    print(f"❌ 连接失败: {e}")
finally:
    # 关闭驱动
    driver.close()
