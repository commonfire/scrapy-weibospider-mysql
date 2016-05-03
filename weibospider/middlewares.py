#-*-coding: utf-8 -*-
import base64
import random
import logging
from  settings import PROXIES 
from scrapy.utils.project import get_project_settings
from mayi_proxy import get_proxy_authHeader
from checkip import check_proxy

class RotateUserAgent():
    '''动态随机设置User_Agent'''
    def __init__(self,user_agents):
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls,crawler):
        return cls(crawler.settings.getlist('USER_AGENTS'))   #调用__init__方法，返回该类的对象

    def process_request(self,request,spider):
        request.headers.setdefault('USER_AGENTS',random.choice(self.user_agents))

class RotateHttpProxy():
    '''动态随机设置代理IP（阿里云-北京地区IP）'''
    def process_request(self,request,spider):
        proxy = random.choice(PROXIES)
        if check_proxy('http',proxy['ip_port']):
            request.meta['proxy'] = 'http://%s' % proxy['ip_port']
            request.meta['work'] = True
            if proxy['user_pass'] is not None:
                # setup basic authentication for the proxy
                encoded_user_pass = base64.encodestring(proxy['user_pass'])
                request.headers['Proxy-Authorization'] = 'Basic' + encoded_user_pass
        else:
            request.meta['work'] = False
   
    def process_exception(self,request,exception,spider):
        proxy = request.meta['proxy']
        logging.info('Removing failed proxy <%s>,%d proxies left' % (proxy,len(PROXIES)-1))  

class MayiHttpProxy():
    '''基于蚂蚁代理设置代理IP'''
    settings = get_project_settings()
    def process_request(self,request,spider):
        #proxy = get_proxy_ip(MayiHttpProxy.settings['APPKEY'],MayiHttpProxy.settings['SECRET'],MayiHttpProxy.settings['SERVERIP'])    #利用蚂蚁代理获取动态代理IP
        #request.meta['proxy'] = 'http://%s' % proxy 
        proxy = MayiHttpProxy.settings['SERVERIP']
        request.meta['proxy'] = 'http://%s' % proxy 
        authHeader = get_proxy_authHeader(MayiHttpProxy.settings['APPKEY'],MayiHttpProxy.settings['SECRET']) 
        request.headers['Proxy-Authorization'] = authHeader
   
    def process_exception(self,request,exception,spider):
        proxy = request.meta['proxy']
        logging.info('Removing failed proxy <%s>' % proxy)  

if __name__=="__main__":
    settings = get_project_settings()
    authHeader = get_proxy_authHeader(settings['APPKEY'],settings['SECRET'])    #利用蚂蚁代理获取动态代理IP
    print authHeader


