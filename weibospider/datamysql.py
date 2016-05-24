#-*- coding:utf-8 -*-
import logging
import sys
import json
import MySQLdb
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)

reload(sys)
sys.setdefaultencoding('utf-8')


class MysqlStore:
    '''Mysql数据库连接与命令操作'''
    settings = get_project_settings()

    def get_connection(self):
        '''连接数据库'''
        try:
            conn = MySQLdb.connect(host=MysqlStore.settings['MYSQL_HOST'],user=MysqlStore.settings['MYSQL_USER'],passwd=MysqlStore.settings['MYSQL_PASSWD'],db=MysqlStore.settings['MYSQL_DBNAME'],port=3306)
            conn.set_character_set('utf8mb4')
            #logger.warning('mysql_connectinon success!!')
            logger.info('mysql_connectinon success!!')
            return conn
        except MySQLdb.Error,e:
            logger.error("Mysql Error %d: %s",(e.args[0],e.args[1]))
        except Exception,e:
            logger.error(e)

    
    def close_connection(self,conn,cursor=None):
        '''关闭数据库'''
        try:
            if cursor:
                cursor.close()
            conn.close()
            logger.info("mysql_connection close!!")
        except MySQLdb.Error,e:
            print "Mysql Error %d: %s" % (e.args[0],e.args[1])

    def update_operation(self,conn,sql,param=None):
        '''更新数据操作'''
        cur = self.set_utf8(conn)
        self.executor(cur,sql,param)
        conn.commit()
        logger.info('update_operation success!!')

    def insert_operation(self,conn,sql,param=None):
        '''插入数据操作'''
        cur = self.set_utf8(conn)
        self.executor(cur,sql,param)
        logger.info('insert_operation success!!')

    def select_operation(self,conn,sql,param=None):
        '''从数据库中选择出数据'''
        cur = self.set_utf8(conn)
        self.executor(cur,sql,param)
        logger.info('select_operation success!!')
        return cur

    def executor(self,cursor,sql,param):
        if param is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,param)

    def set_utf8(self,conn):
        '''设置utf-8字符集'''
        cur = conn.cursor()
        cur.execute('set names utf8;')
        cur.execute('set character set utf8;')
        cur.execute('set character_set_connection=utf8;')
        return cur

if __name__ == '__main__':
    db = MysqlStore();
    conn = db.get_connection();
    #sql3 = "select keyword from cauc_keyword_test where is_search = 1"
    #cursor = db.select_operation(conn,sql3) 
    #a = cursor.fetchall()
    #for i in a:
    #    print i 
    conn.close()
