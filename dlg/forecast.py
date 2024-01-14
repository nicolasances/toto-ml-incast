from flask import Request
from totoapicontroller.TotoDelegateDecorator import toto_delegate
from totoapicontroller.model.UserContext import UserContext
from totoapicontroller.model.ExecutionContext import ExecutionContext
from api.expenses import ExpensesAPI
from config.config import Config

@toto_delegate(config_class=Config)
def forecast_incomes(request: Request, user_context: UserContext, exec_context: ExecutionContext): 
    # Get the Auth Header
    auth_header = request.headers.get('Authorization')
    
    # Call the ExpensesAPI to retrieve the list of incomes
    response = ExpensesAPI(exec_context=exec_context, auth_header=auth_header).get_incomes()
    
    # If there are no incomes, return null
    if response is None or response.incomes is None or len(response.incomes) == 0:
        return {}
    
    # Get the last SALARY (not any income, but the last salary available)
    # Sort the list
    incomes = response.incomes
    incomes.sort(key=lambda income: income.date, reverse=True)
    
    # Only keep salaries
    salaries = [income for income in incomes if income.category == 'SALARY']
    
    if salaries is None or len(salaries) == 0: 
        return {}
    
    return {
        "category": "SALARY", 
        "amount": salaries[0].amount, 
        "currency": salaries[0].currency
    }