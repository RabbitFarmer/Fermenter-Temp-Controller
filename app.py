# Updated app.py file to include a corrected dynamic route for chart rendering for tilt_color
from flask import Flask, jsonify, render_template

app = Flask(__name__)

tilt_data = {
    "red": [23.4, 24.1, 23.8],
    "blue": [22.4, 22.9, 23.1]
}

@app.route('/')
def home():
    return "Welcome to the Fermenter Temperature Controller!"

@app.route('/chart/<tilt_color>')
def show_chart(tilt_color):
    if tilt_color in tilt_data:
        data = tilt_data[tilt_color]
        return render_template('chart.html', data=data, tilt_color=tilt_color)
    else:
        return jsonify({"error": "Invalid tilt color"}), 404

if __name__ == '__main__':
    app.run(debug=True)
