# -*- coding: utf-8 -*-
#python标准模块
import random
import binascii
import logging
import time
#python第三方模块
import base64
import re
import rsa
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request,FormRequest
from scrapy.http.cookies import CookieJar
from scrapy.utils.project import get_project_settings
from weibospider.items import WeibospiderItem
from settings import USER_NAME
#应用程序自定义模块
from analyzer import Analyzer
from analyzers.format_time import *
from analyzers.keyword_info_analyzer import keyword_info_analyzer   
from analyzers.friendcircle_analyzer import friendcircle_analyzer
from analyzers.weibocontent_analyzer import weibocontent_analyzer
from cookielist import COOKIES
from datamysql import MysqlStore
from dataoracle import OracleStore
from friendcircle import FriendCircle
from getpageload import GetWeibopage
from getsearchpage import GetSearchpage
import getinfo

logger = logging.getLogger(__name__)

class WeiboSpider(CrawlSpider):
    '''预警人员库人员微博内容爬虫'''
    name = 'cauc_warningman_weibo'
    allowed_domains = ['weibo.com','sina.com.cn']
    settings = get_project_settings()

    def __init__(self,start_time = None,interval = None,**kwargs):
        self.start_time = start_time
        self.interval = interval

    def start_requests(self):
        return [Request(url="http://weibo.com",method='get',callback=self.start_getweibo_info)]

    def start_getweibo_info(self,response):
        db = MysqlStore();
        #取出没有爬取过的且is_delete=0的重点人员
        GetWeibopage.data['page'] = 1; getweibopage = GetWeibopage()

        for round in range(1): #遍历数据库的轮数
            conn = db.get_connection()
            sql1 = "select user_id from cauc_warning_man_test a \
                    where a.is_search = 0 and a.is_delete = 0"          
            cursor1 = db.select_operation(conn,sql1)
            for user_id in cursor1.fetchall():
                user_id = user_id[0]
                logger.info("this is the unsearched user_id:%s",user_id)
                
                #获取需要爬取的总页面数
                start_time = self.start_time;end_time = get_current_time('day') 
                mainpage_url = "http://weibo.com/" + str(user_id) + "?is_ori=1&is_forward=1&is_text=1&is_pic=1&key_word=&start_time=" + start_time + "&end_time=" + end_time + "&is_search=1&is_searchadv=1&" 
                GetWeibopage.data['uid'] = user_id; 
                thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
                yield  Request(url=thirdload_url,cookies=random.choice(COOKIES),meta={'mainpage_url':mainpage_url,'uid':user_id,'is_search':0},callback=self.parse_total_page)
                

            #取出已经爬取过is_search=1的且is_delete=0的预警人员
            sql2 = "select user_id from cauc_warning_man_test a \
                    where a.is_search = 1 and a.is_delete = 0"
            cursor2 = db.select_operation(conn,sql2)

            for user_id in cursor2.fetchall():
                user_id = user_id[0]
                logger.info("this is the searched user_id:%s",user_id)

                #start_time = get_time_by_interval(int(time.time()),86400,'day');end_time = get_current_time('day') #起始和结束间隔时间为1天(86400s),即过去一天的内容
                start_time = get_time_by_interval(int(time.time()),int(self.interval),'day');end_time = get_current_time('day') #起始和结束间隔时间为x天(由interval代表的秒换算而来)
                mainpage_url = "http://weibo.com/" + str(user_id) + "?is_ori=1&is_forward=1&is_text=1&is_pic=1&key_word=&start_time=" + start_time + "&end_time=" + end_time + "&is_search=1&is_searchadv=1&" 
                GetWeibopage.data['uid'] = user_id; 
                thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
                yield  Request(url=thirdload_url,cookies=random.choice(COOKIES),meta={'mainpage_url':mainpage_url,'uid':user_id,'is_search':1},callback=self.parse_total_page)

            #更新is_search标志位为1
            sql3 = "update cauc_warning_man_test set is_search = 1 where is_search = 0 and is_delete = 0"
            db.update_operation(conn,sql3)
            db.close_connection(conn)

    def parse_total_page(self,response):
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("W_pages")')
        friendcircle_analyzer = keyword_info_analyzer()
        total_pages = friendcircle_analyzer.get_totalpages(total_pq) #需要爬取的微博内容页数
        logger.info("the total_pages is: %d",total_pages)
        
        getweibopage = GetWeibopage()
        mainpage_url = response.meta['mainpage_url']
        user_id = response.meta['uid']
        is_search = response.meta['is_search']

        for page in range(2): #TODO 此处要更改为total_pages
            GetWeibopage.data['uid'] = user_id
            GetWeibopage.data['page'] = page + 1
            firstload_url = mainpage_url + getweibopage.get_firstloadurl()
            yield  Request(url=firstload_url,cookies=random.choice(COOKIES),meta={'uid':user_id,'is_search':is_search},callback=self.parse_load)

            secondload_url = mainpage_url + getweibopage.get_secondloadurl()
            yield  Request(url=secondload_url,cookies=random.choice(COOKIES),meta={'uid':user_id,'is_search':is_search},callback=self.parse_load)

            thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
            yield  Request(url=thirdload_url,cookies=random.choice(COOKIES),meta={'uid':user_id,'is_search':is_search},callback=self.parse_load,dont_filter=True)

    def parse_load(self,response):
        item = WeibospiderItem()  #获取用户微博内容信息
        analyzer = Analyzer()
        friendcircle = FriendCircle()
        total_pq = analyzer.get_html(response.body,'script:contains("WB_feed WB_feed_v3")')
        item['uid'] = response.meta['uid']
        item['content'] = analyzer.get_content(total_pq)
        item['time'],item['timestamp'] = analyzer.get_time(total_pq)

        weibo_analyzer = weibocontent_analyzer()
        item['repost_nums'],item['comment_nums'],item['like_nums'] = weibo_analyzer.get_weibo_relative_args(total_pq)
        yield item     
            
