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
from cookielist import COOKIES
from datamysql import MysqlStore
from dataoracle import OracleStore
from getpageload import GetWeibopage
from getsearchpage import GetSearchpage
import getinfo

logger = logging.getLogger(__name__)

class WeiboSpider(CrawlSpider):
    '''舆情关键词检索爬虫'''
    name = 'cauc_keyword_info'
    allowed_domains = ['weibo.com','sina.com.cn']
    settings = get_project_settings()

    def __init__(self,interval,**kwargs):
        self.interval = interval 

    def start_requests(self):
        return [Request(url="http://weibo.com",method='get',callback=self.search_from_keywordDB)]
    
    def search_from_keywordDB(self,response):
        db = MysqlStore();main_url = "http://s.weibo.com/weibo/"
        getsearchpage = GetSearchpage()
     
        for round in range(1):  #遍历数据库的轮数
            conn = db.get_connection()

            #选取is_search位为0的关键词
            sql1 = "select keyword from cauc_keyword_test_copy where is_search = 0 and is_delete = 0" 
            cursor1 = db.select_operation(conn,sql1)

            #对is_search位为0的关键词进行爬取
            for keyword in cursor1.fetchall():
                keyword = keyword[0]
                logger.info("this is the unsearched keyword:%s",keyword)
                search_url = main_url + getsearchpage.get_searchurl(keyword)
                yield Request(url=search_url,cookies=random.choice(COOKIES),meta={'search_url':search_url,'keyword':keyword},callback=self.parse_total_page)


            #选取is_search位为1的关键词
            sql2 = "select keyword from cauc_keyword_test_copy where is_search = 1 and is_delete = 0" 
            cursor2 = db.select_operation(conn,sql2)

            #对is_search位为1的关键词进行爬取
            for keyword in cursor2.fetchall():
                keyword = keyword[0]
                logger.info("this is the searched keyword:%s",keyword)

                end_time = get_current_time()
                #start_time = get_time_by_interval(int(time.time()),3600)  #爬取3600秒，即1小时前的内容
                start_time = get_time_by_interval(int(time.time()),int(self.interval))  #爬取interval秒前的内容
                
                search_url = main_url + getsearchpage.get_searchurl_time(keyword,start_time,end_time)
                yield Request(url=search_url,cookies=random.choice(COOKIES),meta={'search_url':search_url,'keyword':keyword},callback=self.parse_total_page)

            #更新is_search标志位为1
            sql3 = "update cauc_keyword_test_copy set is_search = 1 where is_search = 0 and is_delete = 0"
            db.update_operation(conn,sql3)
            db.close_connection(conn)
        

    def parse_total_page(self,response):
        '''获取需要爬取的搜索结果总页数'''
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("W_pages")')
        keyword_analyzer = keyword_info_analyzer()
        total_pages = keyword_analyzer.get_totalpages(total_pq)  #需要爬取的搜索结果总页数
        logger.info("the total_pages is: %d",total_pages)
        for page in range(1):  #TODO 此处更改为total_pages
            search_url = response.meta['search_url'] + str(page + 1)  #此处添加for循环total_pages
            yield Request(url=search_url,cookies=random.choice(COOKIES),meta={'keyword':response.meta['keyword']},callback=self.parse_keyword_info)

    def parse_keyword_info(self,response):
        '''获取搜索结果信息'''
        item = WeibospiderItem()
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("feed_content wbcon")') 
        keyword_analyzer = keyword_info_analyzer()
        if total_pq is not None:
            item['keyword_uid'],item['keyword_alias'],item['keyword_content'],item['keyword_publish_time'] = keyword_analyzer.get_keyword_info(total_pq)
            item['keyword'] = response.meta['keyword']
            if item['keyword_uid']: #即此时item['keyword_uid']不为空，有解析内容
                yield item

