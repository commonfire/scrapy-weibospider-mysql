# -*- coding: utf-8 -*-
#python标准模块
import re
import binascii
import logging
import sys
#python第三方模块
import base64
import rsa
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request,FormRequest
from scrapy.http.cookies import CookieJar
from scrapy.settings import Settings
from weibospider import getinfo
from weibospider.login_cookie_fetch import update_cookies,set_flag,clear_flag,write_cookie,user_fetch

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

class WeiboSpider(CrawlSpider):
    name = 'cookie_fetch_periodically'
    allowed_domains = ['weibo.com','sina.com.cn']

    def start_requests(self):
        #clear_flag()                              #flag = 0
        users = user_fetch()
        for user in users:
            username = user['username']
            logger.info('username:'+username)
            username = getinfo.get_user(username)
            url = 'http://login.sina.com.cn/sso/prelogin.php?entry=sso&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&client=ssologin.js(v1.4.4)' % username
            yield Request(url=url,method='get',meta={'cookiejar':CookieJar(),'user':user},callback=self.post_requests)
    
    def close(self):
        code = write_cookie()
        if code:
            set_flag()
        else:
            logger.error('Start Fail!')

    def post_requests(self,response):
        serverdata = re.findall('{"retcode":0,"servertime":(.*?),"pcid":.*?,"nonce":"(.*?)","pubkey":"(.*?)","rsakv":"(.*?)","is_openlock":.*,"exectime":.*}',response.body,re.I)[0]  #获取get请求的数据，用于post请求登录
        servertime = serverdata[0]
        nonce = serverdata[1]
        pubkey = serverdata[2]
        rsakv = serverdata[3]
        user = response.meta['user']
        username = user['username']
        password = user['password']
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
        yield FormRequest(url='http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.4)',formdata=formdata,headers=headers,meta={'cookiejar':response.meta['cookiejar'],'user':user},callback=self.get_cookie)

     
    def get_cookie(self, response):
        p = re.compile('location\.replace\(\'(.*)\'\)')
        try:
            login_url = p.search(response.body).group(1)
            ret_res = re.search('retcode=0',login_url)
            if ret_res:
                logger.info('Login Success!')
            else:
                logger.info('Login Fail!')
        except:
            logger.error('Login Error!')
        request = response.request.replace(url=login_url,meta={'cookiejar':response.meta['cookiejar'],'user':response.meta['user']},method='get',callback=self.save_cookie)  #GET请求login_url获取返回的cookie，后续发送Request携带此cookie
        yield request

    def save_cookie(self, response):
        '''将cookie存入数据库'''
        if (response.status == 200):
            logger.info('Response code:200')
            cookies = []
            user = response.meta['user']
            cookie_jar = response.meta['cookiejar']
            cookie_jar.extract_cookies(response,response.request)
            p = re.compile('(S(.*?)) for .weibo.com\/')

            for cookie in cookie_jar:
                if re.search(p,str(cookie)):
                    cookies.append(re.search(p,str(cookie)).group(1))

            cookies_jar = (cookie.split('=') for cookie in cookies)
            cookie_jar_dict = dict(cookies_jar)
            if cookie_jar_dict:
                update_cookies(user['username'],cookie_jar_dict)
            else:
                logger.info('获取用户'+user['username']+'cookie失败')
        else:
            logger.info('Time out!')


