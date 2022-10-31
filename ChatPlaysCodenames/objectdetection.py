import cv2
import numpy as np
import pytesseract
import os
import windowfinder as wf
from config_loader import Settings
import color_methods as cm
import mouse_control as mc

class ObjectDetector:
    
    def __init__(self):
        
        # load config
        self.confList = Settings().data
        
        # font
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.fontScale = 0.7
        self.color = (0, 0, 255)
        self.thickness = 2
        
        #tesseract config
        self.init_tesseract(self.confList.loc['TESSERACT'].value)
        
        self.image = None
        self.operator_word = None
        self.operator_word_count = 0
        self.team_color = None
    
  
    def init_tesseract(self, path:str):
        if os.path.exists(path): pytesseract.pytesseract.tesseract_cmd = path
    
    def load_image(self, img:np.array):
        self.image = img
        self.area = img.shape[0]*img.shape[1]
        self.w = img.shape[1]
        self.h = img.shape[0]
        
    
    def get_team_color(self):
        
        img_copy = self.image.copy()
        filtered_img_b = cm.convert_to_gray(cm.filter_colors(img_copy, blue=cm.TEAM_BLUE[0], green=cm.TEAM_BLUE[1], red=cm.TEAM_BLUE[2]))
        filtered_img_r = cm.convert_to_gray(cm.filter_colors(img_copy, blue=cm.TEAM_RED[0], green=cm.TEAM_RED[1], red=cm.TEAM_RED[2]))
        if np.sum(filtered_img_b>0) > 1000:
            self.team_color = 'blau'
        elif np.sum(filtered_img_r>0) > 1000:
            self.team_color = 'rot'
        else:
            self.team_color = None
        return self.team_color
    
    def get_operator_contour(self) -> list:
        img_copy = self.image.copy()
        if self.team_color == 'blau':
            filtered_img = cm.filter_colors(img_copy, blue=cm.OPERATOR_BLUE[0], green=cm.OPERATOR_BLUE[1], red=cm.OPERATOR_BLUE[2])
        elif self.team_color == 'rot':
            filtered_img = cm.filter_colors(img_copy, blue=cm.OPERATOR_RED[0], green=cm.OPERATOR_RED[1], red=cm.OPERATOR_RED[2])
        gray_filtered = cm.convert_to_gray(filtered_img)
        bw = cm.process_bin_image(gray_filtered, 1)
        contours = cm.get_contours(bw)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:
                return cv2.boundingRect(cnt)
        return None
    
    def get_operator_word(self) -> list:
        img_copy = self.image.copy()
        gray = cm.convert_to_gray(img_copy)
        x, y, w, h = self.get_operator_contour()
        crop_img = gray[y:y+h, x:x+w]
        text = self.find_texts(img=crop_img,conf=cm.TESS_LINE) 
        words = [w for w in text.split(' ') if w.isalnum()]
        if len(words)>1:
            self.operator_word = words[0]
            self.operator_word_count = words[1]
        else:
            self.operator_word = words[0]
            self.operator_word_count = 0
        return [self.operator_word, self.operator_word_count]
                        
    def find_click_area(self):
                
        x_values = self.get_team_windows()
        conts_s = self.get_stage_contour()
        conts_o = self.get_operator_contour()
        
        x_left = x_values[0][1]
        x_right = x_values[1][0]
        padding = 2
        
        y_top = conts_s[1] + conts_s[3]
        
        if conts_o is None:
            img_copy = self.image.copy()[y_top+padding:,x_left+padding:x_right-padding]
        else:
            y_bot = conts_o[1]
            img_copy = self.image.copy()[y_top+padding:y_bot-padding,x_left+padding:x_right-padding]
        filtered_img = cm.filter_colors(img_copy, blue=255, green=255, red=255)
        gray_filtered = cm.convert_to_gray(filtered_img)
        bw = cm.process_bin_image(gray_filtered, 1)
        contours = cm.get_contours(bw)
        circles = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= 10 and area <= 1000:
                M = cv2.moments(cnt)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                circles.append([cX+x_left,cY+y_top])

        return np.array(circles)[::-1]
    
    def get_stage_contour(self) -> list:
        
        img_copy = self.image.copy()
        gray = cm.convert_to_gray(img_copy)
        bw = cm.process_bin_image(gray, 255)
        contours = cm.get_contours(bw)
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            scal_y = y / self.h
            delta_x = w / self.w
            if (scal_y <= 0.2) and (delta_x >= 0.1):
                return [x, y, w, h]
            
    def get_stage(self) -> str:
        x, y, w, h = self.get_stage_contour()
        img_copy = self.image.copy()
        gray = cm.convert_to_gray(img_copy)
        crop_img = gray[y:y+h, x:x+w]
        return self.find_texts(img=crop_img,conf=cm.TESS_LINES)

                
    def get_team_windows(self) -> list:

        x_minmax = []
        for team in [cm.WINDOW_RED, cm.WINDOW_BLUE]:
            
            img_copy = self.image.copy()
            filtered_img = cm.filter_colors(img_copy, team[0], team[1], team[2])
            
            gray_filtered = cm.convert_to_gray(filtered_img)
            bw = cm.process_bin_image(gray_filtered, 1)
            
            contours = cm.get_contours(bw)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                scale = w / self.w
                if scale > 0.05:
                    x_minmax.append([cnt[:,:,0].min(),cnt[:,:,0].max()])
        return x_minmax
        
    def find_text_area(self) -> list:
        
        x_values = self.get_team_windows()
        conts_s = self.get_stage_contour()
        conts_o = self.get_operator_contour()
        
        x_left = x_values[0][1]
        x_right = x_values[1][0]
        padding = 2
        
        y_top = conts_s[1] + conts_s[3]
        
        if conts_o is None:
            image = self.image.copy()[y_top+padding:,x_left+padding:x_right-padding]
        else:
            y_bot = conts_o[1]
            image = self.image.copy()[y_top+padding:y_bot-padding,x_left+padding:x_right-padding]
        
        gray = cm.convert_to_gray(image)
        bw = cm.process_bin_image(gray, 250)
        contours = cm.get_contours(bw)

        rects = []
        for n, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area > 1000:
                rects.append(cv2.boundingRect(cnt))
                
        return rects, gray

    def get_texts_from_areas(self) -> list:
        areas, img = self.find_text_area()
        text_list = []
        for area in areas:
            x, y, w, h = area
            crop_img = img[y:y+h, x:x+w]
            text = self.find_texts(img=crop_img,conf=cm.TESS_LINE).lower()
            text_list.append(text)
        return text_list[::-1]

    def get_skip_button(self) -> list:
        img_copy = self.image.copy()
        filtered_img = cm.filter_colors(img_copy, blue=cm.CLICK_AREA[0], green=cm.CLICK_AREA[1], red=cm.CLICK_AREA[2])
        gray_filtered = cm.convert_to_gray(filtered_img)
        bw = cm.process_bin_image(gray_filtered, 1)
        contours = cm.get_contours(bw)
        temp_list = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 2000:
                x, y, w, h = cv2.boundingRect(cnt)
                temp_list.append([int(x+w/2),int(y+h/2)])
        temp_array = np.array(temp_list)
        max_y_index = np.argmax(temp_array[:,1])
        return temp_list[max_y_index]
        
    def get_skip_button_approval(self):
        img_copy = self.image.copy()
        filtered_img = cm.filter_colors(img_copy, blue=cm.CLICK_AREA[0], green=cm.CLICK_AREA[1], red=cm.CLICK_AREA[2])
        gray_filtered = cm.convert_to_gray(filtered_img)
        bw = cm.process_bin_image(gray_filtered, 1)
        contours = cm.get_contours(bw)
        temp_list = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 2000:
                x, y, w, h = cv2.boundingRect(cnt)
                temp_list.append([int(x+w/2),int(y+h/2)])
        if len(temp_list) == 2:
            temp_array = np.array(temp_list)
            min_x_index = np.argmin(temp_array[:,0])
            return temp_list[min_x_index]
        else:
            return None
        

    def find_texts(self, img: np.array, conf: str) -> str:
        return pytesseract.image_to_string(img, config=conf, lang=cm.TESS_LAN).strip()

if __name__ == '__main__':   
    od = ObjectDetector()
    od.team_color = 'blau'
    sh = wf.Screenshot()
    sh.check_windows()
    img = sh.take_screenshot()
    od.load_image(img)
    #arr_click = od.find_click_area()
    rec = od.get_skip_button()
    mc.click_at(rec)
    import time
    time.sleep(1)
    img = sh.take_screenshot()
    od.load_image(img)
    rec = od.get_skip_button_approval()
    if rec is not None:
        mc.click_at(rec)
    #mc.click_at(arr_click[textlist.index('schneemann')])
    #cv2.imshow('foo', text_img)
