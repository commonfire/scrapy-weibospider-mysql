# -*- coding: utf-8 -*-
import logging
import sys
import json
from pyquery import PyQuery as pq
import re
import urllib

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

class friendcircle_analyzer:
    '''重点人员朋友圈相关内容解析''' 

    def get_frienduid_url(self,alias):
        '''根据昵称获取用于得到@用户或转发用户uid的请求url'''
        if isinstance(alias,unicode):
            alias = str(alias)
        encoded_alias = urllib.quote(alias)
        return 'http://weibo.com/aj/v6/user/newcard?ajwvr=6&name=%s&type=1' % encoded_alias

    def get_frienduid(self,total_body):
        friend_userinfo = {"code":None,"uid":None,"tag":None}       
        p = re.compile('{"code":"\d*",',re.S)
        match = p.search(unicode(total_body))
        if match:
            code1 = match.group()
            code2 = str(code1).replace(',','}')
            code = json.loads(code2)
            friend_userinfo["code"] = int(code['code'])
            if friend_userinfo["code"] == 100001:   #此时没有该昵称对应的uid
                return friend_userinfo
            else:
                p1 = re.compile('uid=(\d*)&',re.S)
                match1 = p1.search(unicode(total_body))
                if not match1:
                    return friend_userinfo
                else:
                    friend_userinfo["uid"] = int(match1.group(1)) #存储该用户的uid
                    p2 = re.compile('icon_bed',re.S)
                    match2 = p2.search(unicode(total_body))
                    if not match2:
                        friend_userinfo['tag'] = 0  #表示该账号为个人账号
                        return friend_userinfo
                    else:
                        p3 = re.compile('icon_bed.*W_icon icon_pf_approve_co',re.S)
                        match3 = p3.search(unicode(total_body))
                        if not match3:
                            friend_userinfo["tag"] = 0  #表示该账户为个人账号
                            return friend_userinfo
                        else:
                            friend_userinfo["tag"] = 1  #表示该账号为公众账号(不进行爬取操作)
                            return friend_userinfo

        else:
            logging.error("get_frienduid wrong!")
            return None

    def get_userinfo_url(self,uid):
        '''根据用户uid获取请求用户基本信息的请求url'''
        return "http://weibo.com/p/100505" + str(uid) + "/info?mod=pedit_more"

if __name__ == "__main__":
    a = friendcircle_analyzer()
    print a.get_frienduid_url(str(u'航大东北王'))
