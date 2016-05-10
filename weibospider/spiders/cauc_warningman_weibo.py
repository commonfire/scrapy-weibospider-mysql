# -*- coding: utf-8 -*-
#python标准模块
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
    #start_username = settings['USER_NAME']
    start_username = USER_NAME  #登陆用户名
    start_password = settings['PASS_WORD'] #登录用户密码
    #start_uid = settings['UID']

    def __init__(self,start_time = None):
        self.start_time = start_time

    def start_requests(self):
        username = WeiboSpider.start_username
        username = getinfo.get_user(username)
        url = 'http://login.sina.com.cn/sso/prelogin.php?entry=sso&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&client=ssologin.js(v1.4.4)' % username
        return [Request(url=url,method='get',meta={'cookiejar':CookieJar()},callback=self.post_requests)]

    def post_requests(self,response):
        serverdata = re.findall('{"retcode":0,"servertime":(.*?),"pcid":.*?,"nonce":"(.*?)","pubkey":"(.*?)","rsakv":"(.*?)","is_openlock":.*,"exectime":.*}',response.body,re.I)[0]  #获取get请求的数据，用于post请求登录

        servertime = serverdata[0]
        nonce = serverdata[1]
        pubkey = serverdata[2]
        rsakv = serverdata[3]
        username= WeiboSpider.start_username
        password = WeiboSpider.start_password
        formdata = {
            'entry': 'weibo',  
            'gateway': '1',  
            'from': '',  
            'ssosimplelogin': '1',  
            'vsnf': '1',  
            'vsnval': '',  
            'su': getinfo.get_user(username),  
            'service': 'miniblog',  
            'servertime': servertime,  
            'nonce': nonce,  
            'pwencode': 'rsa2',  
            'sp': getinfo.get_pwd(password,servertime,nonce,pubkey),  
            'encoding': 'UTF-8',  
            'prelt': '115',  
            'rsakv': rsakv, 
            'url':'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack', 
            'returntype': 'META'
            }
        headers={'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0 Chrome/20.0.1132.57 Safari/536.11'} 
        return FormRequest(url='http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.4)',formdata=formdata,headers=headers,meta={'cookiejar':response.meta['cookiejar']},callback=self.get_cookie)

     
    def get_cookie(self, response):
        p = re.compile('location\.replace\(\'(.*)\'\)')
        try:
            login_url = p.search(response.body).group(1)
            ret_res = re.search('retcode=0',login_url)
            if ret_res:
                logger.info('Login Success!!!!')
            else:
                logger.error('Login Fail!!!!')
        except:
            print logger.error('Login Error!!!!')
        request = response.request.replace(url=login_url,meta={'cookiejar':response.meta['cookiejar']},method='get',callback=self.start_getweibo_info)  #GET请求login_url获取返回的cookie，后续发送Request携带此cookie
        return request

    def store_cookie(self, response):
        '''存储登陆后获取的cookie'''
        cookie_jar = response.meta['cookiejar']
        cookie_jar.extract_cookies(response,response.request)
        for cookie in cookie_jar:
            print "!!!!",cookie

    def start_getweibo_info(self,response):
        db = MysqlStore();
        #取出没有爬取过的且is_delete=0的重点人员
        GetWeibopage.data['page'] = 1; getweibopage = GetWeibopage()

        for round in range(1): #遍历数据库的轮数
            conn = db.get_connection()

            sql1 = "select user_id from cauc_warning_man_test a \
                    where a.is_search = 0 and a.is_delete = 0"          
            cursor = db.select_operation(conn,sql1)
            for user_id in cursor.fetchall():
                user_id = user_id[0]
                logger.info("this is the unsearched user_id:%s",user_id)
            
                #更新is_search标志位为1
                sql2 = "update cauc_warning_man_test set is_search = 1 where user_id = '%s'" % user_id
                db.update_operation(conn,sql2)
                
                #获取需要爬取的总页面数
                start_time = self.start_time;end_time = get_current_time('hour') 
                mainpage_url = "http://weibo.com/" + str(user_id) + "?is_ori=1&is_forward=1&is_text=1&is_pic=1&key_word=&start_time=" + start_time + "&end_time=" + end_time + "&is_search=1&is_searchadv=1&" 
                GetWeibopage.data['uid'] = user_id; 
                thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
                yield  Request(url=thirdload_url,meta={'cookiejar':response.meta['cookiejar'],'mainpage_url':mainpage_url,'uid':user_id,'is_search':0},callback=self.parse_total_page)
                
            logger.info("current timestamp:%d",int(time.time()))
            #设置循环爬取间隔
            time.sleep(WeiboSpider.settings['WEIBOCONTENT_INTERVAL']) #可以采用间隔15min

            #取出已经爬取过is_search=1的且is_delete=0的预警人员
            sql3 = "select user_id from cauc_warning_man_test a \
                    where a.is_search = 1 and a.is_delete = 0"
            cursor = db.select_operation(conn,sql3)

            for user_id in cursor.fetchall():
                user_id = user_id[0]
                logger.info("this is the searched user_id:%s",user_id)

                start_time = get_time_by_interval(int(time.time()),86400,'hour');end_time = get_current_time('hour') #起始和结束间隔时间为1天(86400s)
                mainpage_url = "http://weibo.com/" + str(user_id) + "?is_ori=1&is_forward=1&is_text=1&is_pic=1&key_word=&start_time=" + start_time + "&end_time=" + end_time + "&is_search=1&is_searchadv=1&" 
                GetWeibopage.data['uid'] = user_id; 
                thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
                #yield  Request(url=thirdload_url,meta={'cookiejar':response.meta['cookiejar'],'mainpage_url':mainpage_url,'uid':user_id,'is_search':1},callback=self.parse_total_page)
            conn.close()

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

        for page in range(1): #TODO 此处要更改为total_pages
            GetWeibopage.data['uid'] = user_id
            GetWeibopage.data['page'] = page + 1
            firstload_url = mainpage_url + getweibopage.get_firstloadurl()
            yield  Request(url=firstload_url,meta={'cookiejar':response.meta['cookiejar'],'uid':user_id,'is_search':is_search},callback=self.parse_load)

            secondload_url = mainpage_url + getweibopage.get_secondloadurl()
            yield  Request(url=secondload_url,meta={'cookiejar':response.meta['cookiejar'],'uid':user_id,'is_search':is_search},callback=self.parse_load)

            thirdload_url = mainpage_url + getweibopage.get_thirdloadurl()
            yield  Request(url=thirdload_url,meta={'cookiejar':response.meta['cookiejar'],'uid':user_id,'is_search':is_search},callback=self.parse_load)

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
        
