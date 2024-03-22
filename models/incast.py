import pandas as pd
import numpy as np
import tensorflow as tf

from tensorflow.keras.layers import Dense, Input, Concatenate
from tensorflow.keras.models import Model
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.metrics import r2_score
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

from totoapicontroller.model.ExecutionContext import ExecutionContext
from totoapicontroller.model.UserContext import UserContext
from totoapicontroller.TotoLogger import TotoLogger
from api.expenses import ExpensesAPI
from store.store import ModelStore

class IncastModel: 
    
    exec_context: ExecutionContext
    logger: TotoLogger
    cid: str
    user_context: UserContext
    
    def __init__(self, exec_context: ExecutionContext, user_context: UserContext) -> None:
        self.exec_context = exec_context
        self.logger = exec_context.logger
        self.cid = exec_context.cid
        self.user_context = user_context;
    
    def train(self, auth_header: str): 
        """Train the Incast Model
        
        Training the data performs the following:
        1. Downloading the data
        2. Preparing the time series for training
        3. Training the model
        4. Scoring the model
        5. Persisting the trained model
        """
        self.logger.log(self.cid, f"Training process started for model Incast")
        
        # 0. Define key parameters
        # T is the number of samples of the time series that are needed for training. T = 5 means that the model will be trained to consider the previous 5 salaries to predict the income of the 6th month.
        T = 5
        
        # 1. Download the data
        response = ExpensesAPI(exec_context=self.exec_context, auth_header=auth_header).get_incomes()
            
        # If there are no incomes, return null
        if response is None or response.incomes is None or len(response.incomes) == 0:
            return {}
        
        incomes = response.incomes
        
        # Only consider the salaries
        salaries_raw = [income for income in incomes if income.category == 'SALARY']
        
        # If there are not enough salaries, return
        # There must be T + 1 salaries, since the (T+1)th salary is used as the label
        if len(salaries_raw) < T + 1: 
            self.logger.log(self.cid, f"Not enough salaries to be able to train the model. Required [{T+1}], got [{len(salaries_raw)}]")
            return {"trained": False, "reason": f"Not enough salaries to be able to train the model. Required [{T+1}], got [{len(salaries_raw)}]"}
        
        # 2. Prepare the data
        salaries = pd.DataFrame([vars(income) for income in salaries_raw])
        
        salaries = salaries[(salaries['category'] == "SALARY") & (salaries['date'] > "20181208")]
        salaries = salaries.drop(columns=["currency", "description", "category"])
        
        # Parse the dates
        salaries['parsed_date'] = pd.to_datetime(salaries['date'], format='%Y%m%d')

        # Sort the data
        salaries_ts = salaries[["parsed_date", "amount"]].set_index("parsed_date").sort_index()
        
        # Running SES
        # We smoothe the data because the combination of spikes in salary (due to bonuses or reimbursements) and lack of a 
        # big amount of data makes it hard for the model to learn
        ses = SimpleExpSmoothing(salaries_ts["amount"])
        fitted_ses = ses.fit(smoothing_level=0.05, optimized=False)

        smoothed_data = fitted_ses.fittedvalues

        salaries_ts['smoothed_amount'] = smoothed_data
        
        # 3. TRAINING
        # --------------------------------------------------------
        # Convert the time series into an array
        series = salaries_ts["smoothed_amount"].values

        X = []
        Y = []

        for t in range(len(salaries_ts) - T):
            training_example = series[t:t+T]
            label = series[t+T]

            X.append(training_example)
            Y.append(label)
            
        # Convert to numpy arrays
        X = np.array(X)
        Y = np.array(Y)

        # Print shapes
        self.logger.log(self.cid, f"Shapes of X and Y: [X: {X.shape} \t Y: {Y.shape}]")
        
        # Split into Train-Val
        N_val = 20

        X_train = X[:-N_val]
        Y_train = Y[:-N_val]
        X_val = X[-N_val:]
        Y_val = Y[-N_val:]

        # Print shapes
        self.logger.log(self.cid, f"Shapes of Training set: [X_train, Y_train: {X_train.shape}, {Y_train.shape}]")
        self.logger.log(self.cid, f"Shapes of Validation set: [X_val, Y_val: {X_val.shape}, {Y_val.shape}]")
        
        # Create the Model
        # Time series
        i = Input(shape=(X.shape[1],))
        x = Dense(40, activation="relu")(i)
        x = Dense(1)(x)

        model = Model(i, x)
        
        model.compile(
            loss='mape',
            optimizer='adam',
        )

        r = model.fit(X_train, Y_train, epochs=300, validation_data=(X_val, Y_val))
        
        # Predict on cross validation to score
        P_val = model.predict(X_val).flatten()
        
        # Calculate the r2 score
        r2 = r2_score(Y_val, P_val)

        self.logger.log(self.cid, f"Model Trained. R2 Score: {r2}")
        
        # --------------------------------------------------------
        # 4. Save the model
        ModelStore(exec_context=self.exec_context).save_model(self.user_context.email, model)
        
        return {"trained": True, "r2Score": r2}