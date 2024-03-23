from flask import Request
from totoapicontroller.TotoDelegateDecorator import toto_delegate
from totoapicontroller.model.UserContext import UserContext
from totoapicontroller.model.ExecutionContext import ExecutionContext
from api.expenses import ExpensesAPI
from config.config import Config
from models.incast import IncastModel

@toto_delegate(config_class=Config)
def forecast_incomes(request: Request, user_context: UserContext, exec_context: ExecutionContext): 
    # Get the Auth Header
    auth_header = request.headers.get('Authorization')
    
    prediction = IncastModel(exec_context=exec_context, user_context=user_context).predict(auth_header=auth_header)
    
    return {
        "category": "SALARY", 
        "amount": prediction["prediction"].__float__(), 
        "currency": "DKK"
    }