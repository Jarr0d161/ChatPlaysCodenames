import cv2
import numpy as np


TEAM_BLUE = [255, 200, 68]
TEAM_RED = [30, 136, 255]

WINDOW_BLUE = [163, 132, 50]
WINDOW_RED = [28, 43, 143]

OPERATOR_BLUE = [233, 202, 123]
OPERATOR_RED = [49, 88, 230]

CLICK_AREA = [0, 228, 255]

BG_NEUTRAL = r'#f4d8b5'
BG_BLUE = r'#3284a3'
BG_RED = r'#8f2b1c'

TESS_LINE = r'--oem 3 --psm 7'
TESS_LINES = r'--oem 3 --psm 6'
TESS_LAN = 'deu'

def process_bin_image(img, limit):
    img = img.copy()
    img[img>=limit] = 255
    img[img<limit] = 0
    return img
  
def convert_to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def filter_colors(color_img:np.array, blue=None, green=None, red=None)->np.array:
    b = color_img[:,:,0:1]
    g = color_img[:,:,1:2]
    r = color_img[:,:,2:3]
    
    li = list()
    for ch in [b, g, r]:
        if blue is None: 
            continue
        else:
            ch = np.where(b!=blue,0,ch)
        
        if green is None: 
            continue
        else:       
            ch = np.where(g!=green,0,ch)
        
        if red is None: 
            continue
        else:       
            ch = np.where(r!=red,0,ch)
        li.append(ch) 
    bg = np.concatenate((li[0], li[1]), axis=2)
    bgr = np.concatenate((bg, li[2]), axis=2)
    return bgr

def get_contours(img):
    cnts = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return cnts[0] if len(cnts) == 2 else cnts[1]