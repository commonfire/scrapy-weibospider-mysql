# -*- coding: utf-8 -*-
#python标准模块
import re
import base64
import binascii
import logging
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
from analyzers.util import get_times_fromdb
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
                print 'Login Success!!!!'
            else:
                print 'Login Fail!!!!'
        except:
            print 'Login Error!!!!'
        request = response.request.replace(url=login_url,meta={'cookiejar':response.meta['cookiejar']},method='get',callback=self.search_from_keywordDB)  #GET请求login_url获取返回的cookie，后续发送Request携带此cookie
        return request

    def store_cookie(self, response):
        '''存储登陆后获取的cookie'''
        cookie_jar = response.meta['cookiejar']
        cookie_jar.extract_cookies(response,response.request)
        for cookie in cookie_jar:
            print "!!!!",cookie
    
    def search_from_keywordDB(self,response):
        db = MysqlStore();conn = db.get_connection()
        main_url = "http://s.weibo.com/weibo/"
        getsearchpage = GetSearchpage()
     
        sql1 = "select keyword from cauc_keyword_test"
        cursor = db.select_operation(conn,sql1)
        for keyword in cursor.fetchall():
            print "this is the keyword:",keyword

        keywords = ['机场 炸弹','飞机 炸弹']
        for i in range(15):
            for keyword in keywords:
                sql3 = "select max(publish_time) from cauc_keyword_info where keyword = '%s'" % keyword  #检查是否爬取过该关键词
                cursor = db.select_operation(conn,sql3)
                newest_time = cursor.fetchone()[0]
                if newest_time is not None:  #已经爬取过该关键词，获取最新时间用于"最新时间-当前时间"时间段内容获取
                    current_time = get_current_time()
                    newest_time = format_time(newest_time)
                    print "爬取过的关键词:%s,搜索时间段%s~%s间的内容" % (keyword,newest_time,current_time)
                    search_url = main_url + getsearchpage.get_searchurl_time(keyword,newest_time,current_time)
                    yield Request(url=search_url,meta={'cookiejar':response.meta['cookiejar'],'search_url':search_url,'keyword':keyword},callback=self.parse_total_page)
                else:   #未爬取过该关键词
                    print "未爬取过的关键词:%s" % keyword
                    search_url = main_url + getsearchpage.get_searchurl(keyword)
                    yield Request(url=search_url,meta={'cookiejar':response.meta['cookiejar'],'search_url':search_url,'keyword':keyword},callback=self.parse_total_page)
            time.sleep(100000)
                
        conn.close()

    def parse_total_page(self,response):
        '''获取需要爬取的搜索结果总页数'''
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("W_pages")')
        keyword_analyzer = keyword_info_analyzer()
        total_pages = keyword_analyzer.get_totalpages(total_pq)  #需要爬取的搜索结果总页数
        for page in range(1):
            search_url = response.meta['search_url'] + str(page + 1)  #此处添加for循环total_pages
            yield Request(url=search_url,meta={'cookiejar':response.meta['cookiejar'],'keyword':response.meta['keyword']},callback=self.parse_keyword_info)

    def parse_keyword_info(self,response):
        '''获取搜索结果信息'''
        item = WeibospiderItem()
        analyzer = Analyzer()
        total_pq = analyzer.get_html(response.body,'script:contains("feed_content wbcon")') 
        keyword_analyzer = keyword_info_analyzer()
        item['keyword_uid'],item['keyword_alias'],item['keyword_content'],item['keyword_publish_time'] = keyword_analyzer.get_keyword_info(total_pq)
        item['keyword'] = response.meta['keyword']
        return item


        
        






