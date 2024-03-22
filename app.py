from flask import Flask, request
from flask_cors import CORS
from config.config import Config
from dlg.forecast import forecast_incomes
from dlg.train import train_incast

# Load the config
Config()

app = Flask(__name__)
CORS(app, origins=["*"])

@app.route('/', methods=['GET'])
def smoke(): 
    return {"api": "toto-ml-incast", "running": True}

@app.route('/predict', methods=['GET'])
def predict_incomes(): 
    return forecast_incomes(request)

@app.route('/train', methods=['POST'])
def train_incast_model(): 
    return train_incast(request)

if __name__ == '__main__':
    app.run()