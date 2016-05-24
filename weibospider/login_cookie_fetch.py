# -*- coding: UTF-8 -*- 
import logging
import MySQLdb
import MySQLdb.cursors
import time
import sys
import json 
import urllib
import os
import hashlib
from weibospider.settings import EXPIRES    
from datamysql import MysqlStore
    
reload(sys)   
sys.setdefaultencoding('utf-8')    

logger = logging.getLogger(__name__)

def user_fetch():
    '''获取账号信息'''
    db = MysqlStore()
    conn = db.get_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    sql = 'SELECT id,username,password FROM cauc_login_account_info'
    nums = cursor.execute(sql)
    users = cursor.fetchallDict()
    conn.commit()
    db.close_connection(conn,cursor)
    if users:
        logger.info('User fetch success!')
        return users
    else:
        logger.error('There is no user in database!')
        

#def cookie_judge(username,expires):
#    cookies = fetch_cookies_from_mysql(username)
#    if (cookies == False):
#        return 0
#    else:
#        timestp_now = time.time()
#        cookie = cookies
        #cookie = json.loads(cookies)

#        if ((timestp_now -int(cookie['timestamp'])) > expires):
#            return 1
#        else:
#            return cookiejar_made(cookie)   

#def cookiejar_made(cookies):
#    cookies.pop("timestamp")
#    return cookies

#def fetch_cookies_from_mysql(username):
#    conn=MySQLdb.connect(host="localhost",user="root",passwd="root",db="spider_test",charset="utf8",cursorclass = MySQLdb.cursors.DictCursor)    
#    cursor = conn.cursor()
#    args = []
#    args.append(md5(username))
#    sql = 'SELECT SUHB,SUB,SUBP,SUE,SUS,SUP,timestamp FROM cookie_info WHERE USERNAME IN (%s)' 
#    in_p  =', '.join(list(map(lambda arg:  "'%s'" % arg, args)))
#    sql = sql % in_p
#    n = cursor.execute(sql)
#    rows = cursor.fetchone()
#    cookies = rows
    #cookies = json.dumps(rows)
#    cursor.close()          
#    conn.commit()  
#    conn.close()
#    if not n:
#        return False    
#    return cookies

#def update_cookies_in_mysql(username,cookies,flag):
#    conn=MySQLdb.connect(host="localhost",user="root",passwd="root",db="spider_test",charset="utf8")
#    timestamp = int(time.time())
#    cursor = conn.cursor()     
#    if (flag == 0):
#        cursor.execute("insert into cookie_info(USERNAME,SUHB,SUB,SUBP,SUE,SUS,SUP,timestamp) values (%s,%s,%s,%s,%s,%s,%s,%s)",(md5(username),cookies['SUHB'],cookies['SUB'],cookies['SUBP'],cookies['SUE'],cookies['SUS'],cookies['SUP'],timestamp))
#    else:
#        cursor.execute("update cookie_info set SUHB=%s,SUB=%s,SUBP=%s,SUE=%s,SUS=%s,SUP=%s,timestamp=%s where USERNAME IN (%s)",(cookies['SUHB'],cookies['SUB'],cookies['SUBP'],cookies['SUE'],cookies['SUS'],cookies['SUP'],timestamp,md5(username)))
#    cursor.close()          
#    conn.commit()  
#    conn.close()

def update_cookies(username,cookies):
    '''更新cookie到数据库'''
    db = MysqlStore()
    conn = db.get_connection()
    timestamp = int(time.time())
    cursor = conn.cursor()
    cursor.execute("insert into cauc_login_cookie_info(USERNAME,SUHB,SUB,SUBP,SUE,SUS,SUP,timestamp) values (%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE SUHB=%s,SUB=%s,SUBP=%s,SUE=%s,SUS=%s,SUP=%s,timestamp=%s",(md5(username),cookies['SUHB'],cookies['SUB'],cookies['SUBP'],cookies['SUE'],cookies['SUS'],cookies['SUP'],timestamp,cookies['SUHB'],cookies['SUB'],cookies['SUBP'],cookies['SUE'],cookies['SUS'],cookies['SUP'],timestamp))
    conn.commit()
    db.close_connection(conn,cursor) 
    logger.info('Update cookies into database...')

def md5(str):
    m = hashlib.md5()   
    m.update(str)
    return m.hexdigest()

def allcookie_fetch():
    '''获取所有cookie'''
    db = MysqlStore()
    conn = db.get_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    nums = cursor.execute('SELECT SUHB,SUB,SUBP,SUE,SUS,SUP,USERNAME FROM cauc_login_cookie_info WHERE (unix_timestamp()-cast(timestamp as signed)) < (%s)',(EXPIRES,))
    rows = cursor.fetchallDict()
    conn.commit()
    db.close_connection(conn,cursor) 
    return nums,rows

def set_flag():
    '''设置flag'''
    db = MysqlStore()
    conn = db.get_connection()
    cursor = conn.cursor()
    sql = "update cauc_parameters set param_value = 1 where param_key = 'flag'"
    n = cursor.execute(sql)
    conn.commit()
    db.close_connection(conn,cursor) 
    if n:
        logger.info('Set flag success!')
    else:
        logger.error('Set flag failed,flag is already 1!')

def clear_flag():
    conn = MysqlStore().get_connection()
    cursor = conn.cursor()
    sql = "update cauc_parameters set param_value = 0 where param_key = 'flag'"
    n = cursor.execute(sql)
    conn.commit()
    db.close_connection(conn,cursor) 
    if n:
        logger.info('clear_flag success!')

def write_cookie():
    '''写入cookielist文件'''
    nums,rows = allcookie_fetch()
    if not nums > 0:
        logger.info('There is no cookie in database!')
        return False
    else:
        path = os.path.abspath('.')+'/weibospider/cookielist.py'
        with open(path,'w+') as f:
            f.write('COOKIES = '+str(rows))
        logger.info('Writing cookies into cookielist.py file...')
        return True




