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

def get_time_by_interval(current_timeStamp,interval):
    '''获取当前时间戳减去时间间隔后的结果时间'''
    subtracted_timeStamp = current_timeStamp - interval
    timeArray = time.localtime(subtracted_timeStamp)
    subtracted_time_otherStyle = time.strftime("%Y-%m-%d-%H",timeArray)
    return subtracted_time_otherStyle 


if __name__ == '__main__':
    timeStamp = int(time.time())           
    interval = 30
    print get_time_by_interval(timeStamp,3600)

    
