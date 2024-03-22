from flask import Request
from totoapicontroller.TotoDelegateDecorator import toto_delegate
from totoapicontroller.model.UserContext import UserContext
from totoapicontroller.model.ExecutionContext import ExecutionContext
from config.config import Config
from models.incast import IncastModel

@toto_delegate(config_class=Config)
def train_incast(request: Request, user_context: UserContext, exec_context: ExecutionContext): 
    """Trains the Incast model for the user specified in the context

    Args:
        request (Request): request (no data needed in the body)
        user_context (UserContext): user context
        exec_context (ExecutionContext): execution context

    Returns:
        _type_: _description_
    """
    # Get the Auth Header
    auth_header = request.headers.get('Authorization')
    
    IncastModel(exec_context=exec_context, user_context=user_context).train(auth_header=auth_header)
    
    return {
        "trained": True
    }