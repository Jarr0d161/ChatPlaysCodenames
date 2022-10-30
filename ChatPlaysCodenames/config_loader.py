import pandas as pd

class Settings:
    
    def __init__(self, path='config.txt'):
        self.data = pd.read_csv(path, sep="=", index_col=0, header=None)
        self.data.columns = ["value"]