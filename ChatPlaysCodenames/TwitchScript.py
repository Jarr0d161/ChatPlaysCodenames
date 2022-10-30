import socket
import threading
from datetime import datetime, timedelta
from message_loader import VoteListener
from config_loader import Settings

class TwitchBot:

    def __init__(self, timer:int, pool:int):
        
        self.encoding = 'utf-8'
        self.confList = Settings().data
        
        self.init_irc()
        self.join_irc()
        
        self.init_threading()
        self.vote_listener = VoteListener()
        
        self.wordlist = list()
        
        self.start_time = datetime.now()
        
        self.time_delta = timedelta(seconds=timer)
        self.pool_limit = pool
        self.most_voted = None
        self.most_voted_counter = 0
        self.bool_voting = False
        
       
    def init_irc(self):
        self.irc_server = self.confList.loc['SERVER'].value
        self.irc_port = int(self.confList.loc['PORT'].value)
        self.irc_access_token = self.confList.loc['AUTH'].value    
        self.irc_name = self.confList.loc['NAME'].value
        self.irc_channel = self.confList.loc['CHANNEL'].value               
        self.irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def init_threading(self):
        self.thread = threading.Thread(target=self.chat_listener)
        self.stop_thread = threading.Event()
        self.start_Event = threading.Event()


    def join_irc(self):
        msg = (
            f'PASS {self.irc_access_token}\n'
            f'NICK {self.irc_name}\n'
            f'JOIN #{self.irc_channel}\n'
            )
        self.irc_socket.connect((self.irc_server, self.irc_port))
        self.irc_socket.send(msg.encode(self.encoding))
        self.joinchat()
        self.irc_socket.send('CAP REQ :twitch.tv/tags\r\n'.encode(self.encoding))


    def sendMessage(self, message):
        messageTemp = f'PRIVMSG #{self.irc_channel} :{message}'
        self.irc_socket.send((f'{messageTemp}\n').encode(self.encoding))


    def joinchat(self):
        Loading = True
        while Loading:
            readbuffer_join = self.irc_socket.recv(1024)
            readbuffer_join = readbuffer_join.decode()
            for line in readbuffer_join.split("\n")[:-1]:
                Loading = self.loadingComplete(line)


    def loadingComplete(self,line) -> bool:
        if('End of /NAMES list' in line):
            print(f'TwitchBot hat sich erfolgreich bei {self.irc_channel} eingewählt!')
            return False
        else:
            return True
    
    
    def get_message_info(self, line) -> list:
        message = None
        user = None
        seperator = 'PRIVMSG'
        last_elements = line.split(seperator)[-1].split(':', 1)
        message = last_elements[1]


        metas = line.split(';')
        for m in metas:
            if m == 'display-name':
                user = m.split('=')[-1]
                break

        return [user, message]
    
                   
    def start_bot(self):
        self.stop_thread.clear()
        self.thread.start()
    

    def stop_bot(self):
        self.stop_thread.set()
        self.thread = None
    
    
    def exit_bot(self):
        if self.thread is not None:
            self.stop_bot()
        self.clear_startEvent()
        self.irc_socket.close()
        
        
    def set_startEvent(self):
        self.start_Event.set()
    
    
    def clear_startEvent(self):
        self.start_Event.clear()
    
    def load_timer(self):
        self.start_time = datetime.now()
    
    def load_wordlist(self, wordlist:list):
        self.wordlist = wordlist
    
    def chat_listener(self):
        while True:
            
            if self.stop_thread.is_set():
                break
            
            delta = datetime.now() - self.start_time
            
            if self.start_Event.is_set():
                if self.most_voted_counter >= self.pool_limit or delta >= self.time_delta:
                    print(f'MostWanted({self.most_voted_counter}): {self.most_voted}, Timedelta: {(datetime.now()-self.start_time)}')
                    self.clear_startEvent()
                    self.vote_listener.clear_loader()
                    self.bool_voting = True
                    
            self.irc_socket.settimeout(5)
            try:
                readbuffer = self.irc_socket.recv(4096).decode()
            except socket.timeout:
                continue
            except OSError:
                break
            
            for line in readbuffer.split('\r\n'):
                if line == '':
                    continue
                if 'PING :tmi.twitch.tv' in line: 
                    self.irc_socket.send('PONG :tmi.twitch.tv\r\n'.encode(self.encoding))
                    continue
                else:
                    user, message = self.get_message_info(line)
                    if self.start_Event.is_set() and message.startswith('!vote'):     
                        split_message = message.split(' ', 1)
                        if len(split_message) == 2 and split_message[0] == '!vote':
                            command = split_message[1].lower()
                            if command in self.wordlist or command == 'skip':
                                self.vote_listener.add_vote(user, command)
                                self.most_voted = self.vote_listener.voting_buffer['word'].value_counts().index.tolist()[0]
                                self.most_voted_counter = self.vote_listener.voting_buffer['word'].value_counts()[0]
                                    
                                    

if __name__ == '__main__':
    bot = TwitchBot()
    bot.set_startEvent()
    t1 = threading.Thread(target = bot.chat_listener())
    t1.start()
