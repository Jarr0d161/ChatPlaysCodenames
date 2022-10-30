import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import objectdetection as od
import TwitchScript as ts
import mouse_control as mc
import time
import windowfinder as wf
import color_methods as cm


class TwitchBotGUI(tk.Frame):
    
    def __init__(self, parent, width=518, height=350, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
               
        alignstr = '%dx%d+%d+%d' % (width, height, 10, 10)
        self.parent.geometry(alignstr)
        self.parent.resizable(width=False, height=False)
        self.parent['bg'] = cm.BG_NEUTRAL
        
        self.state = False
        self.round_count = 0
        self.someButton = None
        self.someBot = None
        self.after_listener = None
        
        self.poolvar = tk.StringVar()
        self.timevar = tk.StringVar()
        
        self.ft = tkFont.Font(family='arial',size=12)
        
        self.init_labels()
        self.init_dropdown_menus()
        self.init_buttons()
        
        self.object_detector = od.ObjectDetector()
        self.init_treeview()
    
    def init_labels(self):
        text_output = r'Vorkehrungen treffen und Bot starten.'
        text_timer = r'Timer fürs Raten [s]:'
        text_counter = r'Anzahl an Nachrichten:'
        
        self.label_output = tk.Label(self.parent,
                                     bg='#ffffff',
                                     fg='#000000',
                                     font=self.ft,
                                     justify=tk.CENTER,
                                     borderwidth=1,
                                     relief=tk.SOLID,
                                     text=text_output)
        self.label_output.place(x=10,y=180)
        
        self.label_input_timer = tk.Label(self.parent,
                                          bg='#ffffff',
                                          fg='#333333',
                                          font=self.ft,
                                          justify=tk.CENTER,
                                          borderwidth=1,
                                          relief=tk.SOLID,
                                          text=text_timer)
        self.label_input_timer.place(x=10,y=220)
        
        self.label_input_counter = tk.Label(self.parent,
                                            bg='#ffffff',
                                            fg='#333333',
                                            font=self.ft,
                                            justify=tk.CENTER,
                                            borderwidth=1,
                                            relief=tk.SOLID,
                                            text=text_counter)
        self.label_input_counter.place(x=10,y=250)
        
    def init_dropdown_menus(self):
               
        timelimits = [30, 60, 90, 120, 180]
        self.timevar.set(str(timelimits[0]))
        self.dropdown_time = tk.OptionMenu(self.parent, self.timevar, *timelimits)
        self.dropdown_time['bg'] = '#ffffff'
        self.dropdown_time.place(x=180, y=220)
        
        poollimits = [5, 10, 25, 50, 100]
        self.poolvar.set(str(poollimits[1]))
        self.dropdown_pool = tk.OptionMenu(self.parent, self.poolvar, *poollimits)
        self.dropdown_pool['bg'] = '#ffffff'
        self.dropdown_pool.place(x=180, y=250)
    
    def init_buttons(self):
        
        self.someButton = tk.Button(self.parent, 
                                    text='Start',
                                    bg='#ffffff',
                                    justify=tk.CENTER,
                                    font=self.ft,
                                    command=self.startButton)
        self.someButton.place(x=330,y=220,width=70,height=30)
        
        tk.Button(self.parent,
                  text='Exit',
                  bg='#ffffff',
                  justify=tk.CENTER,
                  font=self.ft,
                  command=self.exitButton).place(x=420,y=220,width=70,height=30)
    
    
    def init_treeview(self):
        columns = ('column_0','column_1','column_2','column_3','column_4')
        self.tree = ttk.Treeview(self.parent,
                                 columns=columns,
                                 show='headings')
        for col in columns:
            self.tree.column(col, width=50)
        self.tree.place(x=10,y=10, width=500, height=150)
    
    
    def runBot(self):
        texts = self.get_possible_votes()
        words = []
        for count in range(5):
            words.append((texts[5*count],texts[5*count+1],texts[5*count+2],texts[5*count+3],texts[5*count+4]))
        for word in words:
            self.tree.insert('', tk.END, values=word)
        
    def get_possible_votes(self) -> list:
        self.object_detector.load_image(self.get_screenshot())
        return self.object_detector.get_texts_from_areas()
    
    def get_screenshot(self):
        return self.screenshot_maker.take_screenshot()
    
    def check_voting(self):
        if self.someBot.bool_voting:
            mvw = self.someBot.most_voted
            if mvw is not None:
                word = mvw.upper()
            else:
                word = None
            self.someBot.sendMessage(f'SPIELANSAGE: Das Voting ist beendet! Ausgewähltes Wort: {word}')
            self.label_output.config(text=f'Wir haben uns für {word} entschieden.')
            self.someBot.bool_voting = False
            self.someBot.most_voted = None
            self.someBot.most_voted_counter = 0
            self.object_detector.load_image(self.get_screenshot())
            if mvw is not None:
                if mvw != 'skip':
                    textlist = self.object_detector.get_texts_from_areas()
                    arr_click = self.object_detector.find_click_area()
                    mc.click_at(arr_click[textlist.index(mvw)])
                else:
                    mc.click_at(self.object_detector.get_skip_button())
                    time.sleep(1)
                    self.object_detector.load_image(self.get_screenshot())
                    rec = self.object_detector.get_skip_button_approval()
                    if rec is not None:
                        mc.click_at(rec)
                time.sleep(5)
                state = self.get_current_state()
                while state is None:
                    state = self.get_current_state()
                if state==0:
                    self.label_output.config(text=f'Wir sind weiter am Zug und befinden uns in Runde {self.round_count}.')
                    self.listen_to_chat()
                    self.after_listener = self.after(1000, self.check_voting)
                elif state==1:
                    self.stopButton()
                    self.label_output.config(text='Vorkehrungen treffen und Bot starten.')
                else:
                    self.label_output.config(text=r'Wir warten auf die Anderen, die sind meist sehr langsam :/')
                    self.handle_turn()          
        else:
            self.after_listener = self.after(1000, self.check_voting)
        
    def get_current_state(self) -> int:
        try:
            self.object_detector.load_image(self.get_screenshot())
            text = self.object_detector.get_stage()
        except:
            return None
        else:
            if 'versuche' in text.lower():
                return 0
            elif 'gewinnt' in text.lower():
                return 1
            else:
                return 2
    
    def listen_to_chat(self):
        texts = self.get_possible_votes()
        self.someBot.load_wordlist(texts)
        self.someBot.load_timer()
        self.someBot.set_startEvent()
        self.someBot.sendMessage(f'SPIELANSAGE: Möge das Voting beginnen! Ihr habt ab jetzt {self.timevar.get()} Sekunden zeit zu raten.')
    
    def handle_turn(self):
        state = self.get_current_state()
        while state is None:
            state = self.get_current_state()
        if state==0:
            self.round_count += 1            
            time.sleep(7)
            self.label_output.config(text=f'Wir sind am Zug und befinden uns in Runde {self.round_count}.')
            self.listen_to_chat()
            self.after_listener = self.after(1000, self.check_voting)
        elif state==1:
            self.stopButton()
            self.label_output.config(text='Vorkehrungen treffen und Bot starten.')
        else:
            self.label_output.config(text="Wir warten auf die Anderen, die sind meist sehr langsam :/")
            self.after_listener = self.after(1000, self.handle_turn)
        
    def set_team_color(self):
        img = self.get_screenshot()
        self.object_detector.load_image(img)
        return self.object_detector.get_team_color()
    
    def startButton(self):
        self.screenshot_maker = wf.Screenshot()
        checker  = self.screenshot_maker.check_windows()
        if checker == 0:
            self.label_output.config(text='Es wurde kein Codenames Fenster gefunden.')
            return None
        elif checker == 2:
            self.label_output.config(text='Es wurden zuviele Codenames Fenster gefunden.')
            return None
        color = self.set_team_color()
        if color is not None:
            self.startBot()
            if color == 'blau':
                self.parent['bg'] = cm.BG_BLUE
            else:
                self.parent['bg'] = cm.BG_RED
            self.label_output.config(text=f'Du bist Team {color} beigetreten!')
            self.runBot()
            self.handle_turn()
            self.someButton.config(text='Stop', command=self.stopButton)
        else:
            self.label_output.config(text='Bitte einem Team als Ermittler:In beitreten!')
    
    def startBot(self):
        self.someBot = ts.TwitchBot(int(self.timevar.get()), int(self.poolvar.get()))
        self.someBot.start_bot()
    
    def stopButton(self):
        self.stopBot()
        self.init_treeview()
        self.parent["bg"] = cm.BG_NEUTRAL
        self.label_output.config(text='Verbindung getrennt!')
        self.someButton.config(text="Start", command=self.startButton)
    
    def stopBot(self):
        if self.after_listener is not None:
            self.after_cancel(self.after_listener)
        if self.someBot is not None:
            self.someBot.clear_startEvent()
            self.someBot.exit_bot()
        self.someBot = None
        
    def exitButton(self):
        self.stopBot()
        self.parent.destroy()
        

if __name__ == '__main__':
    root = tk.Tk()
    root.title("CHÄD macht alles kaputt!")
    TwitchBotGUI(root).place(x=0,y=0)
    root.mainloop()
