from flask import Flask, request, render_template_string, redirect, url_for  # 导入 Flask 相关模块
import pandas as pd  # 导入 pandas 用于数据处理
import numpy as np  # 导入 numpy 用于数值计算
from pathlib import Path  # 导入 Path 用于路径操作
import subprocess  # 导入 subprocess 用于执行外部脚本
import os  # 导入 os 用于系统操作
import yaml  # 导入 yaml 用于解析 YAML 配置文件
from pgmpy.estimators import BicScore, HillClimbSearch  # 导入贝叶斯网络相关模块
from pgmpy.models import BayesianNetwork  # 导入贝叶斯网络模型
from pgmpy.estimators import MaximumLikelihoodEstimator  # 导入最大似然估计器
from scipy.stats import entropy  # 导入 entropy 用于计算条件熵
import traceback  # 导入 traceback 用于捕获异常堆栈

# 定义路径体系（与 grading_generator.py 完全一致）
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data"  # 基础路径
GRADING_DIR = BASE_DIR / "grading"  # 分级数据路径
CONFIG_DIR = GRADING_DIR / "config"  # 配置文件路径
RISK_PARAMS_PATH = CONFIG_DIR / "risk_parameters.yaml"  # 风险参数文件路径

app = Flask(__name__)  # 初始化 Flask 应用

# ------------------------- 风险分析核心模块 -------------------------
def load_risk_parameters():
    """加载风险计算参数"""
    with open(RISK_PARAMS_PATH) as f:  # 打开风险参数文件
        return yaml.safe_load(f)  # 解析 YAML 文件

def calculate_conditional_entropy(df, target_col):
    """计算条件熵 H(A|C)"""
    grouped = df.groupby('category_id')[target_col].value_counts(normalize=True)  # 按类别分组并计算频率
    cond_entropy = grouped.groupby(level=0).apply(  # 计算条件熵
        lambda x: entropy(x.values, base=2)  # 使用熵公式计算
    )
    return cond_entropy.to_dict()  # 返回条件熵字典

def build_bayesian_network(data):
    """构建贝叶斯网络模型"""
    # 结构学习（使用 pgmpy 0.1.26 的 scoring_method）
    hc = HillClimbSearch(data)  # 先初始化 HillClimbSearch，不传入 scoring_method
    best_model = hc.estimate(scoring_method=BicScore(data))  # 在 estimate 方法中传入 scoring_method

    # 参数学习
    model = BayesianNetwork(best_model.edges())  # 初始化贝叶斯网络
    model.fit(data, estimator=MaximumLikelihoodEstimator)  # 使用最大似然估计器拟合数据
    return model  # 返回构建的模型

def risk_analysis():
    """执行风险分析流程"""
    try:
        print("[1/8] 开始风险分析流程...")

        # 加载必要数据
        print("[2/8] 加载分级数据...")
        grading_df = pd.read_csv(GRADING_DIR / "inital_grading.csv")  # 加载分级数据

        print("[3/8] 加载交叉属性数据...")
        cross_df = pd.read_csv(BASE_DIR / "original_data/cross_attributes.csv")  # 加载交叉属性数据

        # 合并数据（使用 inital_grading.csv 中的 category_id）
        print("[4/8] 合并数据...")
        merged = grading_df.merge(cross_df, on="attribute_code", how="left")  # 左连接合并数据
        if merged.empty:
            raise ValueError("合并后的数据为空，请检查 attribute_code 匹配")

        print("[5/8] 构建贝叶斯网络...")
        model = build_bayesian_network(merged[['attribute_code', 'category_id', 'sensitivity_level']])  # 构建贝叶斯网络

        # 提取条件概率分布
        cpd_dict = {}
        for node in model.nodes():  # 遍历网络节点
            cpd = model.get_cpds(node)  # 获取条件概率分布
            cpd_dict[node] = cpd.values  # 存储概率值

        # 计算风险概率
        print("[6/8] 计算风险指标...")
        merged['P_risk'] = merged.apply(
            lambda row: calculate_risk_probability(row, cpd_dict, load_risk_parameters()),  # 计算风险概率
            axis=1
        )

        # 计算关联强度
        merged['R'] = merged.groupby('category_id')['P_risk'].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-8)  # 避免除零
        )

        # 计算条件熵
        entropy_map = calculate_conditional_entropy(merged, 'sensitivity_level')  # 计算条件熵
        merged['H'] = merged['category_id'].map(entropy_map)  # 映射条件熵

        # 保存结果
        print("[7/8] 保存结果...")
        output_cols = ['attribute_code', 'attribute_chinese', 'sensitivity_level', 'P_risk', 'R', 'H']
        # 检查 merged 数据框中是否包含所有输出列
        available_cols = merged.columns.tolist()
        missing_cols = [col for col in output_cols if col not in available_cols]
        if missing_cols:
            print(f"以下列在合并数据中缺失: {missing_cols}")
            # 可以选择移除缺失的列或者进行其他处理
            output_cols = [col for col in output_cols if col in available_cols]

        merged[output_cols].to_csv(GRADING_DIR / "risk_analysis.csv", index=False)  # 保存风险分析结果

        print("[8/8] 风险分析完成!")
        return merged[output_cols]  # 返回结果数据

    except Exception as e:
        traceback.print_exc()  # 打印异常堆栈
        raise RuntimeError(f"风险分析失败: {str(e)}")  # 抛出异常

def calculate_risk_probability(row, cpd_dict, params):
    """应用公式3.4计算风险概率"""
    # 构建 beta 的键
    beta_key = f"{row['attribute_code']}_{row['category_id']}"

    # 获取参数（带默认值）
    lambda_i = params['lambda'].get(row['attribute_code'], 0.5)  # 获取单属性识别系数
    alpha_ij = params['alpha'].get(row['category_id'], 1.0)  # 获取司法管辖区加权因子
    beta_ij = params['beta'].get(beta_key, 1.0)  # 获取风险影响因子

    # 计算贝叶斯网络联合概率
    node_prob = 1.0
    for node in cpd_dict:  # 遍历条件概率分布
        try:
            # 尝试将 row[node] 转换为整数
            node_value = int(row[node])
            if node in row and node_value < len(cpd_dict[node]):  # 防止索引越界
                prob = cpd_dict[node][node_value]  # 获取概率值
                node_prob *= prob  # 累乘概率
        except (ValueError, TypeError):
            # 如果转换失败，跳过该节点
            continue

    return node_prob * lambda_i * alpha_ij * beta_ij  # 返回风险概率

# ------------------------- Flask路由模块 -------------------------
@app.route('/')
def index():
    return redirect(url_for('grading_management'))  # 重定向到分级管理页面

@app.route('/grading')
def grading_management():
    """分级管理主界面"""
    try:
        grading_df = pd.read_csv(GRADING_DIR / "inital_grading.csv")  # 加载分级数据
        report_content = open(GRADING_DIR / "validation_report.html").read()  # 加载验证报告
        risk_df = pd.read_csv(GRADING_DIR / "risk_analysis.csv") if os.path.exists(GRADING_DIR / "risk_analysis.csv") else pd.DataFrame()  # 加载风险分析结果
    except Exception as e:
        print(f"界面加载错误: {str(e)}")  # 打印错误日志
        grading_df = pd.DataFrame(columns=["attribute_code", "attribute_chinese", "sensitivity_level"])  # 创建空 DataFrame
        report_content = "<p>数据加载失败，请检查后台日志</p>"  # 默认报告内容
        risk_df = pd.DataFrame()  # 创建空 DataFrame

    return render_template_string(
        GRADING_HTML,  # 渲染模板
        data=grading_df.to_dict('records'),  # 传递分级数据
        report=report_content,  # 传递验证报告
        risk_data=risk_df.to_dict('records')  # 传递风险分析数据
    )

@app.route('/generate_grading')
def trigger_grading():
    """触发分级生成"""
    try:
        subprocess.run(
            ["python", os.path.join(os.path.dirname(__file__), "grading_generator.py")],  # 执行生成器脚本
            check=True,  # 检查执行结果
            capture_output=True,  # 捕获输出
            text=True  # 输出为文本
        )
        return redirect(url_for('grading_management'))  # 重定向到分级管理页面
    except Exception as e:
        return render_template_string(ERROR_HTML, error=f"生成失败: {str(e)}"), 500  # 返回错误页面

@app.route('/risk_analysis')
def run_risk_analysis():
    """执行风险分析"""
    try:
        risk_analysis()  # 执行风险分析
        return redirect(url_for('grading_management'))  # 重定向到分级管理页面
    except Exception as e:
        return f"风险分析失败: {str(e)}", 500  # 返回错误信息

# ------------------------- 前端模板 -------------------------
GRADING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>跨境数据分级管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        .container { display: grid; grid-template-columns: 3fr 2fr; gap: 2rem; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f5f7fa; }
        .report-box { background: #f8f9fc; padding: 1.5rem; border-radius: 8px; }
        button { 
            background: #4CAF50; 
            color: white; 
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 2rem;
        }
        button:hover { background: #45a049; }
        .risk-table { margin-top: 2rem; }
        .nav-tabs { margin: 1rem 0; }
        .tab-content { padding: 1rem 0; }
    </style>
</head>
<body>
    <h1>跨境数据属性分级管理</h1>
    <div class="nav-tabs">
        <button onclick="generateGrading()">重新生成分级</button>
        <button onclick="runRiskAnalysis()" style="margin-left:1rem;">属性风险分析</button>
    </div>

    <div class="tab-content">
        <!-- 分级结果 -->
        <div class="container">
            <div>
                <h2>当前分级结果</h2>
                <table>
                    <tr>
                        <th>属性代码</th>
                        <th>属性名称</th>
                        <th>敏感级别</th>
                    </tr>
                    {% for item in data %}
                    <tr>
                        <td>{{ item.attribute_code }}</td>
                        <td>{{ item.attribute_chinese }}</td>
                        <td>{{ item.sensitivity_level }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <div class="report-box">
                <h2>验证报告</h2>
                {{ report|safe }}
            </div>
        </div>

        <!-- 风险分析结果 -->
        <div class="risk-table">
            <h2>风险分析结果</h2>
            <table>
                <tr>
                    <th>属性代码</th>
                    <th>属性名称</th>
                    <th>敏感级别</th>
                    <th>风险概率</th>
                    <th>关联强度</th>
                    <th>条件熵</th>
                </tr>
                {% for item in risk_data %}
                <tr>
                    <td>{{ item.attribute_code }}</td>
                    <td>{{ item.attribute_chinese }}</td>
                    <td>{{ item.sensitivity_level }}</td>
                    <td>{{ "%.4f"|format(item.P_risk) }}</td>
                    <td>{{ "%.2f"|format(item.R) }}</td>
                    <td>{{ "%.3f"|format(item.H) }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <script>
    function generateGrading() {
        if(confirm('确认要重新生成分级吗？这将会覆盖现有数据！')) {
            fetch('/generate_grading')
            .then(response => {
                if (response.ok) {
                    alert('分级生成成功，页面即将刷新');
                    window.location.reload();
                } else {
                    response.text().then(t => alert(t));
                }
            })
            .catch(err => alert('网络错误: ' + err));
        }
    }

    function runRiskAnalysis() {
        if(confirm('确认执行风险分析？该操作可能需要较长时间')) {
            fetch('/risk_analysis')
            .then(response => {
                if (response.ok) {
                    alert('分析完成，页面即将刷新');
                    window.location.reload();
                } else {
                    response.text().then(t => alert(t));
                }
            })
            .catch(err => alert('网络错误: ' + err));
        }
    }
    </script>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h1>操作失败</h1>
    <p style="color: red;">{{ error }}</p>
    <button onclick="window.history.back()">返回</button>
</body>
</html>
"""

if __name__ == "__main__":
    # 初始化目录
    GRADING_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 启动应用
    app.run(port=5001, debug=True, use_reloader=False)