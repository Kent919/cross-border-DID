import numpy as np
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class PolicyGenerator:
    def __init__(self):
        self.driver = GraphDatabase.driver(  # 括号开始
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )  # 括号闭合

    def generate_lsss(self):
        """生成LSSS策略矩阵"""
        with self.driver.session() as session:
            # 获取所有属性
            result = session.run("MATCH (a:Attribute) RETURN a.code as code, a.risk as risk")
            attributes = [(record["code"], record["risk"]) for record in result]
            
            # 构建LSSS矩阵
            size = len(attributes)
            matrix = np.zeros((size, size))
            
            for i, (code, risk) in enumerate(attributes):
                # 行权重 = 风险系数 * 10
                matrix[i][i] = risk * 10
                
                # 获取关联属性
                linked = session.run("""
                    MATCH (a {code: $code})-[r]->(b)
                    RETURN b.code as target
                    """, code=code)
                linked_codes = [record["target"] for record in linked]
                
                # 列位置由关联属性决定
                for j, (target_code, _) in enumerate(attributes):
                    if target_code in linked_codes:
                        matrix[i][j] = 1
            
            return matrix

# 示例用法
if __name__ == "__main__":
    pg = PolicyGenerator()
    lsss_matrix = pg.generate_lsss()
    print("🔐 LSSS策略矩阵：")
    print(lsss_matrix)