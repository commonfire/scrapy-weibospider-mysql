#-*- coding:utf-8 -*-
import time

def get_current_time(scope = None):
    timeStamp = int(time.time())           
    timeArray = time.localtime(timeStamp)
    if scope is None:
        current_time_otherStyle = time.strftime("%Y-%m-%d-%H",timeArray)
        return current_time_otherStyle 
    elif scope == 'day':
        current_time_otherStyle = time.strftime("%Y-%m-%d",timeArray)
        return current_time_otherStyle 
        

 
def format_time(original_time):
    timeArray = time.strptime(original_time,"%Y-%m-%d %H:%M")
    otherStyleTime = time.strftime("%Y-%m-%d-%H",timeArray)
    return otherStyleTime

def get_time_by_interval(current_timeStamp,interval,scope = None):
    '''获取当前时间戳减去时间间隔后的结果时间'''
    subtracted_timeStamp = current_timeStamp - interval
    timeArray = time.localtime(subtracted_timeStamp)
    if scope is None:
        subtracted_time_otherStyle = time.strftime("%Y-%m-%d-%H",timeArray)
        return subtracted_time_otherStyle 
    elif scope == 'day':
        subtracted_time_otherStyle = time.strftime("%Y-%m-%d",timeArray)
        return subtracted_time_otherStyle 
        


if __name__ == '__main__':
    timeStamp = int(time.time())           
    print get_current_time('day')
    print get_time_by_interval(timeStamp,int('86400'),'day')
    

    
