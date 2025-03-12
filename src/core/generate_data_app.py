from flask import Flask, render_template
import generate_data

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate')
def generate():
    result = generate_data.generate_data()
    return result

if __name__ == '__main__':
    app.run(debug=True)
