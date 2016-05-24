# -*- coding: utf-8 -*-
import logging
import sys
import re
from pyquery import PyQuery as pq
reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

class keyword_info_analyzer:
    '''舆情关键词搜索结果解析''' 
    
    def __init__(self):
        self.keyword_uid = []            #与关键词相关的用户uid
        self.keyword_alias = []          #与关键词相关的用户昵称 
        self.keyword_publish_time = []   #与关键词相关用户发表微博时间
        self.keyword_content = []        #与关键词相关用户发表微博内容

    def get_totalpages(self,total_pq):
        '''获取关键词搜索结果总页数'''
        if total_pq is None:  #此时没有页数列表，即只有一页
            return 1
        data = total_pq("div.W_pages").find('li')
        return len(data)
#        total_page = len(data)
#        if total_page == 0:   #此时没有页数列表，即只有一页
#            return 1
#        else:
#            return total_page

    def get_keyword_info(self,total_pq):
        '''获取舆情关键词相关信息'''
        data0 = total_pq("div.search_rese.W_tc")
        if not data0: #此时data0没有匹配结果，表示页面有相关搜索结果
            data1 = total_pq("div.feed_content")
            data2 = total_pq("div.content").children("div.feed_from")
            
            for dku1,dku2 in zip(data1,data2):
                dku1 = pq(dku1)
                dku2 = pq(dku2)

                a_tag = dku1.children('a')
                if len(a_tag) >= 2 and (a_tag.eq(1).attr('class') is not None) and (a_tag.eq(1).attr('class') == "approve_co"):
                    logger.info(" 该账号为企业认证账号company_approve!!")
                    continue
                
                content = dku1.children('p.comment_txt').text() #与关键词相关用户发表微博内容
                self.keyword_content.append(content)
                 
                alias = dku1.find('a').eq(0).attr('nick-name')   #获取舆情关键词相关用户昵称
                self.keyword_alias.append(alias)

                href = dku1.find('a').eq(0).attr('usercard')     #获取舆情关键词相关用户uid
                p = re.compile("id=(\d*)&",re.S)
                match = p.search(unicode(href))
                if match:
                      self.keyword_uid.append(match.group(1))
                else:
                    self.keyword_uid.append("")
                    logger.warning("parse keyuser uid wrong!!")

                time = dku2.find('a').eq(0).attr("title")
                self.keyword_publish_time.append(time)
        else:
            logger.info("没有关键词搜索结果")

        return self.keyword_uid,self.keyword_alias,self.keyword_content,self.keyword_publish_time


if __name__ == '__main__':
    analyzer = keyword_info_analyzer()
    s = """<div class="WB_cardwrap S_bg2 relative">
      <div class="W_pages" suda-data="key=tblog_search_weibo&amp;value=weibo_page">
        <span class="list"><div class="layer_menu_list W_scroll" style="display: none;" node-type="feed_list_page_morelist" action-type="feed_list_page_morelist"><ul><li class="cur"><a href="javascript:void(0);">第1页</a></li><li><a href="/weibo/%25E6%259C%25BA%25E5%259C%25BA%2520%25E7%2582%25B8%25E5%25BC%25B9&amp;typeall=1&amp;suball=1&amp;timescope=custom:2016-04-01-12:2016-04-06-16&amp;nodup=1&amp;page=2" suda-data="key=tblog_search_weibo&amp;value=weibo_page_1">第2页</a></li><li><a href="/weibo/%25E6%259C%25BA%25E5%259C%25BA%2520%25E7%2582%25B8%25E5%25BC%25B9&amp;typeall=1&amp;suball=1&amp;timescope=custom:2016-04-01-12:2016-04-06-16&amp;nodup=1&amp;page=3" suda-data="key=tblog_search_weibo&amp;value=weibo_page_1">第3页</a></li></ul></div> <a href="javascript:void(0);" class="page S_txt1" action-type="feed_list_page_more">第1页<i class="W_ficon ficon_arrow_down S_ficon">c</i></a></span><a href="/weibo/%25E6%259C%25BA%25E5%259C%25BA%2520%25E7%2582%25B8%25E5%25BC%25B9&amp;typeall=1&amp;suball=1&amp;timescope=custom:2016-04-01-12:2016-04-06-16&amp;nodup=1&amp;page=2" suda-data="key=tblog_search_weibo&amp;value=weibo_page_1" class="page next S_txt1 S_line1">下一页</a>
         </div>
            <!-- 未登录提示 -->
              <!-- /未登录提示 --> 
              </div>"""
    s1 = """<div class="WB_cardwrap S_bg2 relative">"""
    total_pq = pq(unicode(s1)) 
    print analyzer.get_totalpages(total_pq)
       
