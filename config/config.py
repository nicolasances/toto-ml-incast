from typing import List
from totoapicontroller.model.TotoConfig import TotoConfig
from totoapicontroller.model.singleton import singleton

from store.store import LoadedModel, ModelStore

@singleton
class Config(TotoConfig):
    
    loaded_models: List[LoadedModel]
    
    def __init__(self): 
        super().__init__()
        
        # Load the model (download it), to avoid the donwload time at inference
        self.loaded_models = ModelStore().download_all()
        
        self.logger.log("INIT", "Configuration loaded.")
        self.logger.log("INIT", f"Loaded [{len(self.loaded_models)}] models.")
        
    def get_api_name(self) -> str:
        return "toto-ml-incast"
    
    def get_model(self, user: str) -> LoadedModel: 
        """Return the trained model (if any) for the specified user

        Args:
            user (str): the email of the user

        """
        for model in self.loaded_models: 
            if model.user == user: 
                return model
            