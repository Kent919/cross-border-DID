from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

# 定义项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

class KnowledgeGraph:
    def __init__(self):
        """初始化Neo4j驱动"""
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )

    def build_graph(self, csv_path):
        """构建带差分隐私的知识图谱"""
        # 从CSV加载数据
        df = pd.read_csv(csv_path)
        
        with self.driver.session() as session:
            # 清空现有数据
            session.run("MATCH (n) DETACH DELETE n")
            
            # 创建属性节点
            for _, row in df.iterrows():
                session.run("""
                    CREATE (a:Attribute {
                        code: $code, 
                        category: $cat,
                        risk: $risk
                    })
                    """, 
                    code=row["属性代码"], 
                    cat=row["类别"], 
                    risk=float(row["隐私风险L"])
                )
            
            # 添加关联边（带差分隐私）
            for _, row in df.iterrows():
                if pd.notna(row["关联属性"]):
                    targets = row["关联属性"].split(";")
                    for target in targets:
                        # 应用差分隐私：20%概率扰动
                        if np.random.rand() < 0.2:
                            continue  # 随机删除部分关联
                        session.run("""
                            MATCH (a {code: $source}), (b {code: $target})
                            CREATE (a)-[r:LINKED]->(b)
                            SET r.strength = $strength
                            """, 
                            source=row["属性代码"], 
                            target=target,
                            strength=np.random.uniform(0.5, 1.0)
                        )

    def visualize(self):
        """生成可视化图谱（需安装Graphviz）"""
        os.system("neo4j-admin store dump --to=src/data/graph.dump")
        print("🔍 可视化图谱已生成：src/data/graph.png")
    
    def apply_differential_privacy(self, epsilon=0.1):
        """应用差分隐私扰动"""
        with self.driver.session() as session:
            # 获取所有边
            edges = session.run("MATCH (a)-[r]->(b) RETURN a.code as source, b.code as target, r.strength as strength")
            edges = [dict(record) for record in edges]
            
            # 对边进行扰动
            for edge in edges:
                if np.random.rand() < epsilon:
                    # 随机删除或修改权重
                    if np.random.rand() < 0.5:
                        session.run("""
                            MATCH (a {code: $source})-[r]->(b {code: $target})
                            DELETE r
                            """, 
                            source=edge["source"], 
                            target=edge["target"]
                        )
                    else:
                        new_strength = np.random.uniform(0.1, 1.0)
                        session.run("""
                            MATCH (a {code: $source})-[r]->(b {code: $target})
                            SET r.strength = $strength
                            """, 
                            source=edge["source"], 
                            target=edge["target"],
                            strength=new_strength
                        )
    
    def calculate_risk_scores(self):
        """计算动态风险评分"""
        with self.driver.session() as session:
            # 获取所有节点
            nodes = session.run("MATCH (a:Attribute) RETURN a.code as code, a.risk as risk")
            nodes = [dict(record) for record in nodes]
            
            # 计算动态权重
            for node in nodes:
                # 示例公式：动态权重 = 风险系数 * 关联强度
                linked_nodes = session.run("""
                    MATCH (a {code: $code})-[r]->(b)
                    RETURN b.code as target, r.strength as strength
                    """, code=node["code"])
                linked_nodes = [dict(record) for record in linked_nodes]
                
                dynamic_weight = node["risk"]
                for link in linked_nodes:
                    dynamic_weight += link["strength"] * 0.1  # 调整权重公式
                
                # 更新节点权重
                session.run("""
                    MATCH (a {code: $code})
                    SET a.dynamic_weight = $weight
                    """, 
                    code=node["code"], 
                    weight=dynamic_weight
                )

# 示例用法
if __name__ == "__main__":
    kg = KnowledgeGraph()
    
    # 构建知识图谱
    kg.build_graph(BASE_DIR / "data/risk_data.csv")
    
    # 应用差分隐私
    kg.apply_differential_privacy(epsilon=0.1)
    
    # 计算动态风险评分
    kg.calculate_risk_scores()
    
    # 可视化图谱
    kg.visualize()