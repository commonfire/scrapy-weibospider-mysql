# -*- coding: utf-8 -*-
#python标准模块
import random
import binascii
import logging
import sys
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

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

class WeiboSpider(CrawlSpider):
    '''重点人员库人员朋友圈(@关系与转发关系)及基本信息爬虫'''
    name = 'cauc_friendcircle_userinfo'
    allowed_domains = ['weibo.com','sina.com.cn']
    settings = get_project_settings()

    def __init__(self,start_time = None,interval = None,**kwargs):
        self.start_time = start_time
        self.interval = interval

    def start_requests(self):
        return [Request(url="http://weibo.com",method='get',callback=self.start_getfriend_info)]

    def start_getfriend_info(self,response):
        db = MysqlStore();
        #取出没有爬取过的且is_delete=0的重点人员
        GetWeibopage.data['page'] = 1; getweibopage = GetWeibopage()

        for round in range(1): #遍历数据库的轮数
            conn = db.get_connection()

            sql1 = "select user_id from cauc_black_man a \
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

            #取出已经爬取过is_search=1的且is_delete=0的重点人员
            sql2 = "select user_id from cauc_black_man a \
                    where a.is_search = 1 and a.is_delete = 0"
            cursor2 = db.select_operation(conn,sql2)

            for user_id in cursor2.fetchall():
                user_id = user_id[0]
                logger.info("this is the searched user_id:%s",user_id)

                #start_time = get_time_by_interval(int(time.time()),86400,'day');end_time = get_current_time('day') #起始和结束间隔时间为1天(86400s)
                start_time = get_time_by_interval(int(time.time()),int(self.interval),'day');end_time = get_current_time('day') #起始和结束间隔时间为x天(由interval代表的秒换算而来)
                mainpage_url = "http://weibo.com/" + str(user_id) + "?is_ori=1&is_forward=1&is_text=1&is_pic=1&key_word=&start_time=" + start_time + "&end_time=" + end_time + "&is_search=1&is_searchadv=1&" 
                GetWeibopage.data['uid'] = user_id; 
                thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
                yield  Request(url=thirdload_url,cookies=random.choice(COOKIES),meta={'mainpage_url':mainpage_url,'uid':user_id,'is_search':1},callback=self.parse_total_page)

            #更新is_search标志位为1
            sql3 = "update cauc_black_man set is_search = 1 where is_search = 0 and is_delete = 0"
            db.update_operation(conn,sql3)
            db.close_connection(conn)


    def parse_total_page(self,response):
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("W_pages")')
        friendcircle_analyzer = keyword_info_analyzer()
        total_pages = friendcircle_analyzer.get_totalpages(total_pq) #需要爬取的微博朋友圈页数
        logger.info("the total_pages is: %d",total_pages)
        
        getweibopage = GetWeibopage()
        mainpage_url = response.meta['mainpage_url']
        user_id = response.meta['uid']
        is_search = response.meta['is_search']

        for page in range(1): #TODO 此处要更改为total_pages
            GetWeibopage.data['uid'] = user_id
            GetWeibopage.data['page'] = page + 1
            firstload_url = mainpage_url + getweibopage.get_firstloadurl()
            yield  Request(url=firstload_url,cookies=random.choice(COOKIES),meta={'uid':user_id,'is_search':is_search},callback=self.parse_load)

            secondload_url = mainpage_url + getweibopage.get_secondloadurl()
            yield  Request(url=secondload_url,cookies=random.choice(COOKIES),meta={'uid':user_id,'is_search':is_search},callback=self.parse_load)

            thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
            yield  Request(url=thirdload_url,cookies=random.choice(COOKIES),meta={'uid':user_id,'is_search':is_search},callback=self.parse_load)

    def parse_load(self,response):
        request_url = response.request.url
        p=re.compile('&pre_page=(\d).*&page=(\d)')  #用于判断是第一页的第一次加载
        match = p.search(request_url)
        if match:
            if int(match.group(1)) == 0 and int(match.group(2)) == 1: #进行当前主用户信息的获取(即非@用户和转发用户)
                is_search = response.meta['is_search']
                if not is_search: #没有搜索过该主用户，则is_search=0
                    analyzer = Analyzer()
                    total_pq = analyzer.get_html(response.body,'script:contains("PCD_person_info")')
                    user_property = analyzer.get_userproperty(total_pq)
                    if not user_property == 'icon_verify_co_v': #该账号不为公众账号
                        userinfo_url = analyzer.get_userinfohref(total_pq)
                        yield Request(url=userinfo_url,cookies=random.choice(COOKIES),meta={'uid':response.meta['uid'],'is_friend':0},callback=self.parse_userinfo)

        item = WeibospiderItem()  #获取用户微博信息及@用户与转发信息
        analyzer = Analyzer()
        friendcircle = FriendCircle()
        total_pq = analyzer.get_html(response.body,'script:contains("WB_feed WB_feed_v3")')
        item['uid'] = response.meta['uid']
        item['content'] = analyzer.get_content(total_pq)
        item['time'],item['timestamp'] = analyzer.get_time(total_pq)

        weibo_analyzer = weibocontent_analyzer()
        item['repost_nums'],item['comment_nums'],item['like_nums'] = weibo_analyzer.get_weibo_relative_args(total_pq)


        atuser_info,item['repost_user'] = analyzer.get_atuser_repostuser(total_pq)
        atuser_list = friendcircle.atuser_parser(atuser_info)
        item['atuser_nickname_list'] = atuser_list
        yield item     
        
        frc_analyzer = friendcircle_analyzer()
        #获取@用户uid及基本信息
        atuser_set = self.get_atuser_set(atuser_list)
        for atuser_alias in atuser_set:
            friend_url = frc_analyzer.get_frienduid_url(atuser_alias)
            yield Request(url=friend_url,cookies=random.choice(COOKIES),meta={'uid':response.meta['uid'],'is_friend':1},callback=self.parse_friend_uid) #is_friend=1代表爬取@用户基本信息 
       
    #获取转发用户uid及基本信息
        for repostuser_alias in item['repost_user']:
            if repostuser_alias: #repostuser_alias不为空，即有转发用户
                friend_url = frc_analyzer.get_frienduid_url(repostuser_alias)
                yield Request(url=friend_url,cookies=random.choice(COOKIES),meta={'uid':response.meta['uid'],'is_friend':2},callback=self.parse_friend_uid) #is_friend=2代表爬取转发用户基本信息 



    def parse_friend_uid(self,response):
        '''根据昵称解析朋友圈用户uid'''
        frc_analyzer = friendcircle_analyzer()
        friend_json_info = frc_analyzer.get_frienduid(response.body)

        if friend_json_info and friend_json_info['code'] != 100001:
            if friend_json_info['uid'] and friend_json_info['tag'] == 0: #获取朋友圈非公众账号个人信息
                print "the friend uid:",friend_json_info['uid']
                userinfo_url = frc_analyzer.get_userinfo_url(friend_json_info['uid'])
                yield Request(url=userinfo_url,cookies=random.choice(COOKIES),meta={'uid':friend_json_info['uid'],'is_friend':response.meta['is_friend']},callback=self.parse_userinfo,dont_filter=True)
            else:
                logger.warning('no right uid found for alias!')
        else:
            logger.warning('no right uid found for alias!')
        

    def parse_userinfo(self,response):
        '''解析非公众账号个人信息 '''
        item = WeibospiderItem()
        analyzer = Analyzer()
        try:
            total_pq1 = analyzer.get_html(response.body,'script:contains("pf_photo")')
            item['image_urls'] = analyzer.get_userphoto_url(total_pq1) + "?uid=" + str(response.meta['uid'])
            #item['image_urls'] = None 
             
            total_pq2 = analyzer.get_html(response.body,'script:contains("PCD_text_b")')
            total_pq3 = analyzer.get_html(response.body,'script:contains("PCD_counter")')

            if response.meta['is_friend'] == 0: #此时用于获取主用户基本信息，而非朋友圈用户基本信息
                item['userinfo'] = analyzer.get_userinfo(total_pq2,total_pq3)
            elif response.meta['is_friend'] == 1: #此时用于获取@用户基本信息
                item['atuser_userinfo'] = analyzer.get_userinfo(total_pq2,total_pq3)
            else: #此时用于获取转发用户基本信息
                item['repostuser_userinfo'] = analyzer.get_userinfo(total_pq2,total_pq3)

        except Exception,e:
            item['userinfo'] = {}.fromkeys(('昵称：'.decode('utf-8'),'所在地：'.decode('utf-8'),'性别：'.decode('utf-8'),'博客：'.decode('utf-8'),'个性域名：'.decode('utf-8'),'简介：'.decode('utf-8'),'生日：'.decode('utf-8'),'注册时间：'.decode('utf-8'),'follow_num','follower_num'),'')
            item['atuser_userinfo'] = item['userinfo'] 
            item['repostuser_userinfo'] = item['userinfo']
            item['image_urls'] = None

        finally:
            item['uid'] = response.meta['uid']
            yield item  
        
    def get_atuser_set(self,atuser_list):
        result = []
        for atuser_inner_list in atuser_list:
            result.extend(atuser_inner_list)
        return set(result)


