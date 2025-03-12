from flask import Flask, render_template, request
import generate_data
import config_manager

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate')
def generate():
    result = generate_data.generate_data()
    return result

@app.route('/config')
def config():
    params = config_manager.read_config_file()
    return render_template('config.html', params=params)

@app.route('/save_config', methods=['POST'])
def save_config():
    params = config_manager.read_config_file()
    for param in params:
        param_id = param["param_id"]
        new_value = request.form.get(param_id)
        param["func_value"] = new_value
    config_manager.save_config_file(params)
    return "配置保存成功！"

if __name__ == '__main__':
    app.run(debug=True)
