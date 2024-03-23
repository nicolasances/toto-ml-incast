
import os
from typing import List

from flask import request
import requests
from config.config import Config
from totoapicontroller.model.ExecutionContext import ExecutionContext

class TotoIncome: 
    amount: float
    description: str 
    date: str 
    currency: str 
    category: str 
    
    def __init__(self, amount: float, description: str, date: str, currency: str, category: str) -> None:
        self.amount = amount
        self.description = description
        self.date = date
        self.currency = currency
        self.category = category
    
    @classmethod
    def from_dict(cls, data): 
        return TotoIncome(data.get('amount', 0), data.get('description'), data.get('date'), data.get('currency'), data.get('category'))

class GetIncomesResponse: 
    incomes: List[TotoIncome]
    
    def __init__(self) -> None:
        self.incomes = []
        
    def add_income(self, income: TotoIncome): 
        self.incomes.append(income)
    
    @classmethod
    def from_json(cls, data): 
        response = GetIncomesResponse()
        
        if data is None or data.get('incomes') is None: 
            return response
        
        for income in data.get('incomes'):
            response.add_income(TotoIncome.from_dict(income))
        
        return response
    
    def to_dict(self) -> dict:
        return {
            'incomes': [income.__dict__ for income in self.incomes]
        }

class ExpensesAPI: 
    
    endpoint: str
    exec_context: ExecutionContext
    auth_header: str
    
    def __init__(self, exec_context: ExecutionContext, auth_header: str) -> None:
        # Set the endpoint data
        self.endpoint = os.environ.get('EXPENSES_API_ENDPOINT')
        
        # Set passed vars
        self.exec_context = exec_context
        self.auth_header = auth_header
        
    def get_salaries(self, depth: int = 0) -> GetIncomesResponse: 
        """Retrieves the list of incomes of the specified user
        
        Returns:
            GetIncomesResponse: the response of the service
        """
        response = requests.get(
            f"{self.endpoint}/incomes?category=SALARY&last={depth}", 
            headers={
                "Accept": "application/json", 
                "Authorization": self.auth_header, 
                "x-correlation-id": self.exec_context.cid
            }
        )
        
        if response.status_code == 200: 
            return GetIncomesResponse.from_json(response.json())
        else: 
            self.exec_context.logger.log(self.exec_context.cid, f"ExpensesAPI generated an ERROR with code [{response.status_code}] and message [{response.text}]")
            return None
        
