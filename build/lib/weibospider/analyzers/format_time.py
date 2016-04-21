#-*- coding:utf-8 -*-
import time

def get_current_time():
    timeStamp = int(time.time())           
    timeArray = time.localtime(timeStamp)
    current_time_otherStyle = time.strftime("%Y-%m-%d-%H",timeArray)
    return current_time_otherStyle 
    
def format_time(original_time):
    timeArray = time.strptime(original_time,"%Y-%m-%d %H:%M")
    otherStyleTime = time.strftime("%Y-%m-%d-%H",timeArray)
    return otherStyleTime


