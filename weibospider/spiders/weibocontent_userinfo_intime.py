# -*- coding: utf-8 -*-
#python标准模块
import re
import base64
import rsa
import binascii
import logging
from urllib import quote
#python第三方模块
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request,FormRequest
from scrapy.utils.project import get_project_settings
from weibospider.items import WeibospiderItem
from scrapy.conf import settings
from settings import USER_NAME
#应用程序自定义模块
import getinfo
import userinfo
from analyzer import Analyzer
from dataoracle import OracleStore
from friendcircle import FriendCircle
from getpageload import GetWeibopage

logger = logging.getLogger(__name__)


class WeiboSpider(CrawlSpider):
    '''输入用户uid，获取用户基本信息与发表微博内容'''
    #settings.set('ITEM_PIPELINES',{'weibospider.user_imagepipelines.UserImagesPipeline':None,'weibospider.oracle_pipelines.WeibospiderPipeline':300},priority='spider') 
    name = 'weibocontent_userinfo_intime'
    allowed_domains = ['weibo.com','sina.com.cn']
    settings = get_project_settings()
    #start_username = settings['USER_NAME']
    start_username = USER_NAME
    start_password = settings['PASS_WORD']
    #start_uid = settings['UID']
    page_num = settings['PAGE_NUM']
    follow_page_num = settings['FOLLOW_PAGE_NUM']


    def __init__(self,uid = None,per_page_num = None):
        self.uid = uid
        self.per_page_num = per_page_num
        self.atuser_dict = {}

    def closed(self,reason):
        db = OracleStore();conn = db.get_connection()
        cur = conn.cursor()
        for key in self.atuser_dict.keys(): #插入@用户uid信息
            sql= """update t_user_weibocontent_atuser set atuserID = %s where userID = %s and atuser = '%s'""" % (self.atuser_dict.get(key),self.uid,key)
            cur.execute(sql)
            conn.commit()

        sql = '''update t_spider_state set contentstate = 1'''
        db.insert_operation(conn,sql)
        print '------weibocontent_info_spider closed------'                                                                                                               
   
    def start_requests(self):
        username = WeiboSpider.start_username
        username = getinfo.get_user(username)
        url = 'http://login.sina.com.cn/sso/prelogin.php?entry=sso&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&client=ssologin.js(v1.4.4)' % username
        return [Request(url=url,method='get',callback=self.post_requests)]

    def post_requests(self,response):
        serverdata = re.findall('{"retcode":0,"servertime":(.*?),"pcid":.*?,"nonce":"(.*?)","pubkey":"(.*?)","rsakv":"(.*?)","is_openlock":.*,"exectime":.*}',response.body,re.I)[0] #获取get请求的数据，用于post请求登录
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
        return [FormRequest(url='http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.4)',formdata=formdata,headers=headers,callback=self.get_cookie)]

     
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

        request = response.request.replace(url=login_url,meta={'cookiejar':1},method='get',callback=self.start_getweiboinfo)  #GET请求login_url获取返回的cookie，后续发送Request携带此cookie
        return request


    def start_getweiboinfo(self,response):
        mainpageurl = 'http://weibo.com/u/'+str(self.uid)+'?from=otherprofile&wvr=3.6&loc=tagweibo&is_all=1&'
        GetWeibopage.data['uid'] = self.uid    
        getweibopage = GetWeibopage()
        for page in range(int(self.per_page_num),int(self.per_page_num)+2): 
            GetWeibopage.data['page'] = page
            firstloadurl = mainpageurl + getweibopage.get_firstloadurl()
            yield  Request(url=firstloadurl,meta={'cookiejar':response.meta['cookiejar'],'uid':self.uid},callback=self.parse_load)

            secondloadurl = mainpageurl + getweibopage.get_secondloadurl()
            yield  Request(url=secondloadurl,meta={'cookiejar':response.meta['cookiejar'],'uid':self.uid},callback=self.parse_load)
           
            thirdloadurl = mainpageurl + getweibopage.get_thirdloadurl()
            yield  Request(url=thirdloadurl,meta={'cookiejar':response.meta['cookiejar'],'uid':self.uid},callback=self.parse_load)           


    def parse_load(self,response):
        request_url = response.request.url
        p=re.compile('&pre_page=(\d).*&page=(\d)')  #用于判断是第一页的第一次加载
        match = p.search(request_url)
        if int(match.group(1)) == 0 and int(match.group(2)) == 1: #进行用户信息的获取
            db = OracleStore();conn = db.get_connection()
            sql = "select count(*) from (select userID from t_user_info where userID='%s' union select userID from t_publicuser_info where userID='%s')" % (self.uid,self.uid)
            cursor = db.select_operation(conn,sql);count = cursor.fetchone()
            if not count[0]:  #若没有爬取过该uid用户,则爬取用户基本信息
                analyzer = Analyzer()
                total_pq =  analyzer.get_html(response.body,'script:contains("PCD_person_info")')
                user_property = analyzer.get_userproperty(total_pq)
                if user_property == 'icon_verify_co_v': #该账号为公众账号
                    public_userinfo_url = analyzer.get_public_userinfohref(total_pq)
                    yield Request(url=public_userinfo_url,meta={'cookiejar':response.meta['cookiejar'],'uid':response.meta['uid'],'user_property':user_property},callback=self.parse_public_userinfo) 
                else:
                    userinfo_url = analyzer.get_userinfohref(total_pq)
                    yield Request(url=userinfo_url,meta={'cookiejar':response.meta['cookiejar'],'uid':response.meta['uid'],'user_property':user_property},callback=self.parse_userinfo)
            db.close_connection(conn,cursor)

        item = WeibospiderItem()  #获取用户微博信息及@用户信息
        analyzer = Analyzer()
        friendcircle = FriendCircle()
        total_pq =  analyzer.get_mainhtml(response.body)
        item['uid'] = response.meta['uid']
        item['content'] = analyzer.get_content(total_pq)
        item['time'],item['timestamp'] = analyzer.get_time(total_pq)
        atuser_info,item['repost_user'] = analyzer.get_atuser_repostuser(total_pq)
        atuser_list = friendcircle.atuser_parser(atuser_info)
        item['atuser_nickname_list'] = atuser_list
        yield item
      
        for atuser_inlist in atuser_list:
            if atuser_inlist != []: #某微博没有@用户
                for atuser in atuser_inlist:  
                    uid_url = "http://s.weibo.com/user/"+quote(quote(str(atuser)))+"&Refer=weibo_user"
                    yield Request(url=uid_url,meta={'cookiejar':response.meta['cookiejar'],'uid':self.uid,'atuser_nickname':atuser},callback=self.parse_atuser_uid)
            else:
                continue


    def parse_atuser_uid(self,response):
        '''解析对应@用户的uid'''
        item = WeibospiderItem()
        analyzer = Analyzer()
        friendcircle = FriendCircle()
        atuser_nickname = response.meta['atuser_nickname'];
        total_pq = analyzer.get_html(response.body,'script:contains("W_face_radius")') 
        #uid = friendcircle.get_user_uid(total_pq)
        atuser_uid = friendcircle.get_user_uid2(atuser_nickname,total_pq) #根据昵称获取@用户uid
        self.atuser_dict[atuser_nickname] = atuser_uid


    def parse_userinfo(self,response):
        '''解析非公众账号个人信息'''
        item = WeibospiderItem()
        analyzer = Analyzer()
        try:
            total_pq1 = analyzer.get_html(response.body,'script:contains("pf_photo")')
            #item['image_urls'] = analyzer.get_userphoto_url(total_pq1)
            item['image_urls'] = None 
             
            total_pq2 = analyzer.get_html(response.body,'script:contains("PCD_text_b")')
            item['userinfo'] = analyzer.get_userinfo(total_pq2)
        except Exception,e:
            item['userinfo'] = {}.fromkeys(('昵称：'.decode('utf-8'),'所在地：'.decode('utf-8'),'性别：'.decode('utf-8'),'博客：'.decode('utf-8'),'个性域名：'.    decode('utf-8'),'简介：'.decode('utf-8'),'生日：'.decode('utf-8'),'注册时间：'.decode('utf-8')),'')
            item['image_urls'] = None

        item['uid'] = response.meta['uid']
        item['user_property'] = response.meta['user_property']
        yield item  

    def parse_public_userinfo(self,response):  
        '''解析公众账号个人信息'''
        item = WeibospiderItem()
        analyzer = Analyzer()
        try:
            total_pq1 = analyzer.get_html(response.body,'script:contains("pf_photo")')
            #item['image_urls'] = analyzer.get_userphoto_url(total_pq1)
            item['image_urls'] = None 
            item['userAlias_public'] = total_pq1("div.PCD_header")("h1").text()

            total_pq2 = analyzer.get_html(response.body,'script:contains("PCD_text_b")') 
            item['userinfo'] = analyzer.get_public_userinfo(total_pq2)
        except Exception,e:
            item['userinfo'] = {}.fromkeys(('联系人：'.decode('utf-8'),'电话：'.decode('utf-8'),'邮箱：'.decode('utf-8'),'友情链接：'.decode('utf-8')),'')   
            item['image_urls'] = None
            item['userAlias_public'] = ""

        item['uid'] = response.meta['uid']
        item['user_property'] = response.meta['user_property']
        yield item
