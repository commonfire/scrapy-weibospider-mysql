#-*-coding: utf-8 -*-
import sys
from urllib import urlencode,quote

reload(sys)
sys.setdefaultencoding('utf-8')


class GetSearchpage:
    '''获取指定关键词搜索网页的url'''
    data = {
        'nodup':'1',
        'page':'',
    }

    def get_searchurl(self,keyword):
        encoded_keyword = quote(quote(keyword))        
        return encoded_keyword+'&'+urlencode(GetSearchpage.data)

    def get_searchurl_time(self,keyword,start_time,end_time):
        """获取基于时间段的关键词搜索url"""
        encoded_keyword = quote(quote(keyword))        
        timescope = 'timescope=custom:' + start_time + ':' + end_time
        return encoded_keyword+'&' + timescope + '&' +urlencode(GetSearchpage.data)

#http://s.weibo.com/weibo/%25E8%258C%2583%25E5%2586%25B0%25E5%2586%25B0&timescope=custom:2015-09-24-11:2016-04-10-11&page=1&nodup=1

if __name__ == "__main__":
    a = GetSearchpage()
    #print a.get_searchurl('空闹')
    print a.get_searchurl_time('空闹','2015-09-24-11','2016-04-10-11')

