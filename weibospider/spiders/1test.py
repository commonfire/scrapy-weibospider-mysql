# -*- coding: utf-8 -*-
#python标准模块
import random
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
from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from settings import USER_NAME
#应用程序自定义模块
import getinfo
from analyzer import Analyzer
from cookielist import COOKIES
from dataoracle import OracleStore
from getpageload import GetWeibopage
from dataoracle import OracleStore

logger = logging.getLogger(__name__)

class WeiboSpider(CrawlSpider):
    name = '1test'
    allowed_domains = ['weibo.com','sina.com.cn']

    def spider_closed(self,spider,reason):
        logger.info("spider closed....")
        #SpiderClass = type(spider)
        #self.crawlerProcess.crawl(SpiderClass())
        

    def start_requests(self):
        return [Request(url='http://weibo.com',method='get',cookies=random.choice(COOKIES),callback=self.logined)]

    def logined(self,response):
        if response.status == 200:
            logger.info("response succeed!!")
            logger.warning("the succeed response code %d!!",response.status)
            print "status code:",response.status
            print "$$$$$$$$$$$",response.request.cookies
        #return [Request(url='http://weibo.com/p/100202read9305179',meta={'cookiejar':response.meta['cookiejar']},callback=self.logined1)]
        else:
            logger.warning("the failed response status code %d!!",response.status)
            return [Request(url='http://weibo.com',method='get',cookies=random.choice(COOKIES),callback=self.logined)]

        return [Request(url='http://weibo.com/p/100202read9305179',cookies=random.choice(COOKIES),callback=self.logined1)]

    def logined1(self,response):
        print "##########",response.request.cookies
        with open('test_page.html','w+') as f:
            f.write(str(response.body))
        return 

    def post_requests(self,response):
        try:
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
        except:
            #logger.info("the current proxy ip_port is: %s not worked",response.request.meta['proxy'])
            print "wrong"

     
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
        request = response.request.replace(url=login_url,meta={'cookiejar':response.meta['cookiejar']},method='get',callback=self.test)  #GET请求login_url获取返回的cookie，后续发送Request携带此cookie
        return request

    def test(self, response):
        print "do nothing, just testing.."
#        cookie_jar = response.meta['cookiejar']
#        cookie_jar.extract_cookies(response,response.request)
#        for cookie in cookie_jar:
#            print "!!!!",cookie
