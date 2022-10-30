import pandas as pd

class VoteListener:
    
    def __init__(self):
        
        self.COLUMN_NAMES = ['user', 'word']
        self.voting_buffer = pd.DataFrame(columns=self.COLUMN_NAMES)
        
    def add_vote(self, user:str, word:str):
        if self.check_user(user):
            self.voting_buffer = self.voting_buffer[self.voting_buffer['user'].str.contains(user)==False]
        new_row = {'user':user, 'word':word}
        self.voting_buffer = self.voting_buffer.append(new_row, ignore_index=True)
        
    def check_user(self, user:str) -> bool:
        return (self.voting_buffer['user'].eq(user)).any()
    
    def get_votelist(self) -> pd.DataFrame:
        return self.voting_buffer
   
        
    def clear_loader(self):
        self.voting_buffer = pd.DataFrame(columns=self.COLUMN_NAMES)