from flask import Flask, request
from flask_cors import CORS
from dlg.forecast import forecast_incomes


app = Flask(__name__)
CORS(app, origins=["*"])

@app.route('/', methods=['GET'])
def smoke(): 
    return {"api": "toto-ml-incast", "running": True}

@app.route('/predict', methods=['GET'])
def predict_incomes(): 
    return forecast_incomes(request)


if __name__ == '__main__':
    app.run()