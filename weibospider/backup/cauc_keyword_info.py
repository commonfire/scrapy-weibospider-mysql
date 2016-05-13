# -*- coding: utf-8 -*-
#python标准模块
import re
import base64
import binascii
import logging
import time
#python第三方模块
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
    #start_username = settings['USER_NAME']
    start_username = USER_NAME  #登陆用户名
    start_password = settings['PASS_WORD'] #登录用户密码
    #start_uid = settings['UID']


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
        request = response.request.replace(url=login_url,meta={'cookiejar':response.meta['cookiejar']},method='get',callback=self.search_from_keywordDB)  #GET请求login_url获取返回的cookie，后续发送Request携带此cookie
        return request

    def store_cookie(self, response):
        '''存储登陆后获取的cookie'''
        cookie_jar = response.meta['cookiejar']
        cookie_jar.extract_cookies(response,response.request)
        for cookie in cookie_jar:
            print "!!!!",cookie
    
    def search_from_keywordDB(self,response):
        db = MysqlStore();main_url = "http://s.weibo.com/weibo/"
        getsearchpage = GetSearchpage()
     
        for round in range(1):  #遍历数据库的轮数
            conn = db.get_connection()

            #对is_search位为0的关键词进行爬取
            sql1 = "select keyword from cauc_keyword_test_copy where is_search = 0"
            cursor = db.select_operation(conn,sql1)
            for keyword in cursor.fetchall():
                keyword = keyword[0]
                logger.info("this is the unsearched keyword:%s",keyword)
                #更新is_search标志位为1
                sql2 = "update cauc_keyword_test_copy set is_search = 1 where keyword = '%s'" % keyword
                db.update_operation(conn,sql2)
                search_url = main_url + getsearchpage.get_searchurl(keyword)
                yield Request(url=search_url,meta={'cookiejar':response.meta['cookiejar'],'search_url':search_url,'keyword':keyword},callback=self.parse_total_page)

            logger.info("current timestamp:%d",int(time.time()))
            #设置循环爬取间隔
            time.sleep(WeiboSpider.settings['KEYWORD_INTERVAL']) #可以采用间隔15min 

            #对is_search位为1的关键词进行爬取
            sql3 = "select keyword from cauc_keyword_test_copy where is_search = 1"
            cursor = db.select_operation(conn,sql3)
            for keyword in cursor.fetchall():
                keyword = keyword[0]
                logger.info("this is the searched keyword:%s",keyword)

                end_time = get_current_time()
                start_time = get_time_by_interval(int(time.time()),3600)  #爬取3600秒，即1小时前的内容
                
                search_url = main_url + getsearchpage.get_searchurl_time(keyword,start_time,end_time)
                yield Request(url=search_url,meta={'cookiejar':response.meta['cookiejar'],'search_url':search_url,'keyword':keyword},callback=self.parse_total_page)
            conn.close()

    def parse_total_page(self,response):
        '''获取需要爬取的搜索结果总页数'''
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("W_pages")')
        keyword_analyzer = keyword_info_analyzer()
        total_pages = keyword_analyzer.get_totalpages(total_pq)  #需要爬取的搜索结果总页数
        logger.info("the total_pages is: %d",total_pages)
        for page in range(1):  #TODO 此处更改为total_pages
            search_url = response.meta['search_url'] + str(page + 1)  #此处添加for循环total_pages
            yield Request(url=search_url,meta={'cookiejar':response.meta['cookiejar'],'keyword':response.meta['keyword']},callback=self.parse_keyword_info)

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
                return item

