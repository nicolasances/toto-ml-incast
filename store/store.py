from math import log
import time 
import json
import os
import pickle
import re
import tempfile
from typing import List
from google.cloud import storage
from totoapicontroller.model.ExecutionContext import ExecutionContext
from totoapicontroller.TotoLogger import TotoLogger
from totoapicontroller.model.TotoConfig import TotoConfig
from keras.models import load_model

class TrainingDataStore: 
    
    def __init__(self, exec_context: ExecutionContext) -> None:
        self.logger = exec_context.logger
        self.cid = exec_context.cid
        
class LoadedModel: 
    
    user: str
    model: any
    
    def __init__(self, user: str, model: any) -> None:
        self.user = user
        self.model = model

class ModelStore: 
    
    logger: TotoLogger
    
    def __init__(self, exec_context: ExecutionContext = None) -> None:
        self.client = storage.Client()
        self.bucket = self.client.bucket(os.environ["MODELS_BUCKET"])
        if exec_context != None: 
            self.logger = exec_context.logger
            self.cid = exec_context.cid
        
    
    def save_model(self, user: str, model: any):
        
        self.logger.log(self.cid, f"Saving trained Incast model for user [{user}]")
        
        # Define the filepath
        filepath = f"incast/incast-{user}.keras"
        
        # Locally dump the model
        local_temp_file = f"incast-{user}.keras"
        
        model.save(local_temp_file)
            
        # Upload to the bucket
        blob = self.bucket.blob(filepath)
        
        blob.upload_from_filename(local_temp_file)
        
        self.logger.log(self.cid, f"Incast model for user [{user}] saved under filepath [{filepath}]")
        
        return filepath

    
    def load_model_and_vocab(self, user: str): 
        """Loads in-memory the Uncast model for the user

        Args:
            user (str): the user (email)

        Returns:
            (model, dict): a tuple containing the loaded model and a dictionnary that contains the download and load times
        """
        # Define files to download
        model_filepath = f"incast/incast-{user}.keras"
        
        # Download the files
        download_start_time = time.time()
        
        model_blob = self.bucket.blob(model_filepath)
        
        target_model_file = f"incast-{user}.keras"
        
        model_blob.download_to_filename(target_model_file)
        
        download_time = time.time() - download_start_time
        
        # Load the model
        load_start_time = time.time()
        
        loaded_model = load_model(target_model_file)
            
        load_time = time.time() - load_start_time
        
        return loaded_model, {"download_time": download_time, "load_time": load_time}
    
    
    def get_users_list(self) -> list:
        """Retrieves the list of users that have a trained model saved on GCS

        Returns:
            list: the list of str (users' emails)
        """
        # File prefix, to use to only select the model files for the expcat model
        prefix = "incast/incast-"
        
        # List the files in the bucket
        blobs = self.bucket.list_blobs(prefix=prefix)
        
        # For each file, extract the filename and the the user
        users = [blob.name[len(prefix):-len(".keras")] for blob in blobs]
        
        return users
    
    def download_all(self) -> List[LoadedModel]:
        """Downloads all model and vocab files for all users

        Returns:
            list: a list of LoadedModel
        """
        # Gets the list of users
        users = self.get_users_list()
        
        # For each user, download the model
        loaded_models = []
        
        for user in users: 
            model, _ = self.load_model_and_vocab(user)
            loaded_models.append(LoadedModel(user, model))
        
        return loaded_models