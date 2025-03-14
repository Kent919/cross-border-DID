# File: src/core/test_route.py
from flask import Flask

# 初始化 Flask 应用
app = Flask(__name__)

# 定义测试路由
@app.route('/test')
def test():
    return "Hello, Flask!"

# 运行应用
if __name__ == "__main__":
    app.run(port=5001, debug=True)