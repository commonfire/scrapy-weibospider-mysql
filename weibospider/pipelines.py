# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from twisted.enterprise import adbapi
import logging
import MySQLdb
import sys
from scrapy.utils.project import get_project_settings
import getinfo
import re
reload(sys)
sys.setdefaultencoding('utf8')


class WeibospiderPipeline(object):
    
    settings = get_project_settings()
    start_uid = settings['UID']

    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):
        dbargs = dict(
            host = settings['MYSQL_HOST'],
            db = settings['MYSQL_DBNAME'],
            user = settings['MYSQL_USER'],
            passwd = settings['MYSQL_PASSWD'],
            charset = 'utf8mb4',
        )
        dbpool = adbapi.ConnectionPool('MySQLdb',**dbargs)
        return cls(dbpool)
   
    def process_item(self,item,spider):
        if spider.name == 'cauc_keyword_info': #舆情关键词检索信息插入
            d = self.dbpool.runInteraction(self._keyword_info_insert,item,spider)
        elif spider.name == 'cauc_friendcircle_userinfo':  #重点人员朋友圈信息插入
            d = self.dbpool.runInteraction(self._friendcircle_info_insert,item,spider)
        d.addErrback(self._handle_error,item,spider) 
        d.addBoth(lambda _:item)
        return d
    
    def _keyword_info_insert(self,conn,item,spider):
        '''舆情关键词检索信息插入'''
        for i in range(len(item['keyword_uid'])):
            conn.execute('''insert ignore into cauc_keyword_info(user_id,user_alias,keyword,publish_time,content,content_md5) values(%s,%s,%s,%s,%s,md5(%s))''',(item['keyword_uid'][i],item['keyword_alias'][i],str(item['keyword']),item['keyword_publish_time'][i],item['keyword_content'][i],item['keyword_content'][i])) #设置符合主键实现insert ignore的不重复插入

    def _friendcircle_info_insert(self,conn,item,spider):
        '''重点人员朋友圈信息及该重点人员个人信息插入'''
        if 'userinfo' in item:
            self._userinfo_insert(conn,item,spider,'main') #插入主用户个人基本信息
        elif 'friend_userinfo' in item:
            self._userinfo_insert(conn,item,spider,'friend') #插入朋友圈个人基本信息
        else:    
            self._friendcirle_insert_helper(conn,item)  #插入朋友圈关系信息

    def _friendcirle_insert_helper(self,conn,item):
        for i in range(len(item['content'])):
            if item['atuser_nickname_list'][i] != {}:
                for atuser in item['atuser_nickname_list'][i]:
                    conn.execute('''insert ignore cauc_microblog_atuser_info(user_id,atuser_alias,publish_time,publish_timestamp) values(%s,%s,%s,%s)''',(str(item['uid']),atuser,item['time'][i],item['timestamp'][i]))

    def _userinfo_insert(self,conn,item,spideri,type):
        '''微博主用户个人信息插入'''
        if item['image_urls']:  #item['image_urls']不为None
            if 'png' not in item['image_urls']:
                imageurl = "images/userphoto/full/"+str(item['uid'])+".jpg"
                thumbnail_url = "images/userphoto/thumbs/small/"+str(item['uid'])+"_thumbnail.jpg" 
            else:
                tmp = item['image_urls']
                imageurl = "images/userphoto/full/"+tmp[tmp.rindex('/')+1:tmp.rindex('.')]+".jpg"
                thumbnail_url = "images/userphoto/thumbs/small/"+tmp[tmp.rindex('/')+1:tmp.rindex('.')]+"_thumbnail.jpg"
        else:
            imageurl = '';thumbnail_url = ''

        if type == 'main': #插入主用户个人基本信息
            conn.execute('''insert into cauc_microblog_user(user_id,user_alias,location,sex,blog,domain,brief,birthday,register_time,head_image,small_head_image,follow_num,follower_num) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(str(item['uid']),item['userinfo']['昵称：'.decode('utf-8')],item['userinfo']['所在地：'.decode('utf-8')],item['userinfo']['性别：'.decode('utf-8')],item['userinfo']['博客：'.decode('utf-8')],item['userinfo'.decode('utf-8')]['个性域名：'.decode('utf-8')],item['userinfo']['简介：'.decode('utf-8')],item['userinfo']['生日：'.decode('utf-8')],item['userinfo']['注册时间：'.decode('utf-8')],imageurl,thumbnail_url,item['userinfo']['follow_num'],item['userinfo']['follower_num']))
        else:  #插入朋友圈用户个人信息
            conn.execute('''insert ignore into cauc_microblog_atuser(user_id,user_alias,location,sex,blog,domain,brief,birthday,register_time,head_image,small_head_image,follow_num,follower_num) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(str(item['uid']),item['friend_userinfo']['昵称：'.decode('utf-8')],item['friend_userinfo']['所在地：'.decode('utf-8')],item['friend_userinfo']['性别：'.decode('utf-8')],item['friend_userinfo']['博客：'.decode('utf-8')],item['friend_userinfo'.decode('utf-8')]['个性域名：'.decode('utf-8')],item['friend_userinfo']['简介：'.decode('utf-8')],item['friend_userinfo']['生日：'.decode('utf-8')],item['friend_userinfo']['注册时间：'.decode('utf-8')],imageurl,thumbnail_url,item['friend_userinfo']['follow_num'],item['friend_userinfo']['follower_num'])) #user_alias为主键


    def _handle_error(self,failure,item,spider):
        logging.error(failure)  

