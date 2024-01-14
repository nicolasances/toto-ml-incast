from totoapicontroller.model.TotoConfig import TotoConfig
from totoapicontroller.model.singleton import singleton

@singleton
class Config(TotoConfig):
    
    def __init__(self): 
        super().__init__()
        
        self.logger.log("INIT", "Configuration loaded.")
        
    def get_api_name(self) -> str:
        return "toto-ml-incast"