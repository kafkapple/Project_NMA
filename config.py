from dataclasses import dataclass, field
import os
import sys
import datetime
from collections import namedtuple
import re

# dropout
# bath norm
# optimizer adam
# activation relu
# early stop 5 epoch (loss)

# scheduler at train_utils CosineAnnealingLR
# torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)



def generate_unique_path(base_path, is_file=False, version_prefix='_v'):
    """
    Generates a unique path by appending a version number if the path already exists.

    Args:
    base_path (str): The base path of the file or folder.
    is_file (bool): Whether the path is for a file. If False, it is considered a folder.
    version_prefix (str): The prefix to use for versioning. Default is '_v'.

    Returns:
    str: The unique path.
    """
    # If the path does not exist, return the base path
    if not os.path.exists(base_path):
        return base_path

    # Extract the name and extension for files
    if is_file:
        name, ext = os.path.splitext(base_path)
        counter = 1
        new_path = base_path
        
        # Generate a unique file name
        while os.path.exists(new_path):
            new_path = f"{name}{version_prefix}{counter}{ext}"
            counter += 1
        return new_path
    else:
        counter = 1
        new_path = base_path
        
        # Generate a unique folder name
        while os.path.exists(new_path):
            new_path = f"{base_path}{version_prefix}{counter}"
            counter += 1
        return new_path

@dataclass

#
class Config:
    mask_time_length =2
    n_unfreeze=10
    device=''
    
    # monitoring
    N_STEP_FIG: int = 2
    N_EMBEDDINGS: int = 2000 # n of embeddings to show

    VISUALIZE = False # during training 
    
    N_SAMPLE=500 # for toy sampling?
    
    NUM_EPOCHS: int = 5
    BATCH_SIZE: int = 32
    lr: float = 0.0005 #1e-4 ~ 1e-3
    weight_decay: float = 0.0005 #0.1 # 1e-5 ~ 1e-4
    # Model settings
    DATA_NAME= "RAVDESS"#_audio_speech"
    MODEL: str = "classifier_only"#"wav2vec_pretrained"#"wav2vec_v2" "classifer" "wav2vec_finetuned"
    model_name: str = ''
    
    # os.path.join('wav2vec_I_fine_tune_best')
    path_pretrained="facebook/wav2vec2-base" # model pretrained
    
    ACTIVATION: str = "relu"
    OPTIMIZER: str = "adam"
    # For regul
    DROPOUT_RATE: float = 0.4
    early_stop_epoch: int = 100
    label_smoothing=0.1
    momentum = 0.1
    
    BOOL_REGUL = True
    BOOL_MODEL_INIT=False
    
    SCHEDULER: bool = BOOL_REGUL
    GRADIENT_CLIP: bool = BOOL_REGUL
    eta_min: float = 1e-4 /100
    
    MODEL_INIT: bool = BOOL_MODEL_INIT # no need for finetuning
    
    dataset={"RAVDESS": "https://zenodo.org/record/1188976/files/Audio_Speech_Actors_01-24.zip?download=1",
         "MELD": "https://huggingface.co/datasets/declare-lab/MELD/resolve/main/MELD.Raw.tar.gz",
         "MELD_toy": "https://huggingface.co/datasets/declare-lab/MELD/resolve/main/MELD.Raw.tar.gz"}
    # select_dataset = "RAVDESS"
    
    if DATA_NAME=="MELD_toy":
        N_SAMPLE = 30
 
    CUR_MODE: str ='' # current mode

    # General settings
    SEED: int = 2024

    global_epoch:int = 0
    
    history: dict = field(default_factory=lambda: {
        'train': {'loss': [], 'accuracy': [], 'precision': [], 'recall': [], 'f1': []},
        'val': {'loss': [], 'accuracy': [], 'precision': [], 'recall': [], 'f1': []}
    })
    
    # Data settings
    RATIO_TRAIN: float = 0.7
    RATIO_TEST: float = 0.15
    
    LABELS_EMOTION: dict = field(default_factory=lambda: {
        0: 'neutral', 1: 'calm', 2: 'happy', 3: 'sad',
        4: 'angry', 5: 'fearful', 6: 'disgust', 7: 'surprised'
    })
    LABELS_EMO_MELD: dict = field(default_factory=lambda: {
        0: 'anger', 1: 'disgust', 2: 'fear', 3: 'joy',
        4: 'neutral', 5: 'sadness', 6: 'surprise'
    })
    
    LABELS_EMOTION_TEXT: dict = field(default_factory=lambda:{
        'sadness': 0, 'anger': 1, 'love': 2, 'surprise': 3, 'fear': 4, 'joy': 5
        })
    # Paths
    PROJECT_DIR: str = "Project"#"NMA_Project_SER"
    BASE_DIR: str = field(init=False)
    DATA_DIR: str = field(init=False)
    MODEL_DIR: str = field(init=False)
    MODEL_SAVE_PATH: str = field(init=False)
    CKPT_SAVE_PATH: str = field(init=False)
    extracted_path: str = ''
    TARGET:str ='test'
    
    # Metric
    EvaluationResult = namedtuple('EvaluationResult', ['loss', 'accuracy', 'precision', 'recall', 'f1', 'labels', 'predictions'])
    METRIC_AVG='weighted'
    
    # Wandb settings
    IS_RESUME: bool = False
    WANDB_PROJECT: str = ''#field(init=False)
    ENTITY: str = "biasdrive-neuromatch"
    id_wandb: str = ""
    sweep_id: str =""
    IS_SWEEP: bool = False
    SWEEP_NAIVE: bool =True
    N_SWEEP: int = 50
    
    model_benchmark='svm'
    C_val: float = 1#0.1
    max_iter: int = 1000 # for multi logistic reg
    solver: str = 'saga'
    penalty: str = 'l2'#'elasticnet'
    kernel: str = 'rbf'
    gamma: int = 0.001
    
    sweep_config = {
        'method': 'bayes',
        'metric': {'goal': 'maximize', 'name': 'val.loss' },
        'parameters': {
            'lr': {'min': 0.0001, 'max': 0.01},
            'batch_size': {'values': [16, 32, 64, 128]},
            'dropout_rate': {'min': 0.1, 'max': 0.6},
            "activation":{"values":['relu', 'leaky_relu', 'gelu']},
            #'optimizer': {'values': ['adam', 'SGD']},
           # 'num_epochs': {'min': 5, 'max': 50},
        }
    }
    
    CONFIG_DEFAULTS = {
    "resume":"allow",
    "dataset": DATA_NAME,
    "epochs": NUM_EPOCHS,
    "global_epoch": global_epoch,
    "batch_size": BATCH_SIZE,
    "model": MODEL,
    "lr": lr,
    "dropout_rate": DROPOUT_RATE,
    "activation": ACTIVATION,
    "optimizer": OPTIMIZER,
    "regularization_add": BOOL_REGUL,
    "model_initialization": BOOL_MODEL_INIT
    }  
    def __post_init__(self):
        current_date = datetime.datetime.now()
        date_str = current_date.strftime("%Y%m%d")
        
        # Get current script path
        project_dir= os.path.dirname(os.path.abspath(__file__))

        #project_dir = os.path.dirname(current_dir)
        os.chdir(project_dir)

        # add project path to Python module seasrch path Project 
        sys.path.insert(0, project_dir)
        
        self.BASE_DIR = project_dir#os.path.join(os.path.dirname(os.getcwd()), self.PROJECT_DIR)
        self.DATA_DIR = os.path.join(self.BASE_DIR, 'data')
        self.MODEL_BASE_DIR=os.path.join(self.BASE_DIR, 'models')
        os.makedirs(self.BASE_DIR, exist_ok=True)
        os.makedirs(self.MODEL_BASE_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.update_path()
        
    def update_path(self):
        self.DATA_FULL_DIR = os.path.join(self.DATA_DIR, self.DATA_NAME)
        self.WANDB_PROJECT=f"{self.MODEL}_{self.DATA_NAME}"
        #self.WANDB_PROJECT = f"{self.PROJECT_DIR}_{self.MODEL}"#_{date_str}"
        self.MODEL_DIR = os.path.join(self.MODEL_BASE_DIR, self.WANDB_PROJECT, self.WANDB_PROJECT)
        
            # file_name = file_name.replace('best_model_', '')
        if os.path.exists(self.MODEL_DIR):
            self.MODEL_DIR = generate_unique_path(self.MODEL_DIR, is_file=False)
            print(f'New model stuffs will be saved: {self.MODEL_DIR}\n')
            
        self.MODEL_RESULTS = os.path.join(self.MODEL_DIR, 'results')
        self.MODEL_PRE_BASE_DIR = os.path.join(self.MODEL_DIR, 'finetuned')
        
        self.MODEL_SAVE_PATH = os.path.join(self.MODEL_DIR, f'best_model_{self.WANDB_PROJECT}.pth')
        self.CKPT_SAVE_PATH = os.path.join(self.MODEL_DIR, f'checkpoint_{self.WANDB_PROJECT}.pth')
        self.best_model_info_path = os.path.join(self.MODEL_BASE_DIR, 'best_model_info.txt')
        
        if os.path.exists(self.MODEL_SAVE_PATH):
            self.MODEL_SAVE_PATH = generate_unique_path(self.MODEL_SAVE_PATH, is_file=True)#generate_unique_filename(self.MODEL_SAVE_PATH)
            self.CKPT_SAVE_PATH = generate_unique_path(self.CKPT_SAVE_PATH, is_file=True)#generate_unique_filename(self.CKPT_SAVE_PATH)
            print(f'New model will be saved: {self.MODEL_SAVE_PATH}')
            # file_name, _ = os.path.splitext(os.path.basename(self.MODEL_SAVE_PATH))
        ####
        #self.path_pretrained = os.path.join(self.MODEL_BASE_DIR, 'wav2vec_I_fine_tune_best')


        print(f'\n\n##### Current Project Location #####\n-Base Directory: {self.BASE_DIR}\n-Data: {self.DATA_FULL_DIR}\n-Current Model: {self.MODEL_DIR}\n-Current Model name: {self.MODEL_SAVE_PATH}\n\nFigure will be saved per {self.N_STEP_FIG}-step\n')
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        os.makedirs(self.MODEL_RESULTS, exist_ok=True)
        os.makedirs(self.MODEL_PRE_BASE_DIR, exist_ok=True)
        os.makedirs(self.DATA_FULL_DIR, exist_ok=True)
        
    # def __setattr__(self, name:str, value: any) -> None:
    #     if hasattr(self, name):
    #         old_value = getattr(self, name)
    #         if old_value != value:
    #             print(f"Updating {name}: {old_value} -> {value}")
    #     super().__setattr__(name, value)
    def print_variables(self):
        for var, value in self.__dict__.items():
            if not var.startswith("_"):  # 
                print(f"{var}: {value}")

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: {key} is not a valid config variable")

#config = Config()