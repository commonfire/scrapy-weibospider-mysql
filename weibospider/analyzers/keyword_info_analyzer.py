# -*- coding: utf-8 -*-
import re
from pyquery import PyQuery as pq
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class keyword_info_analyzer:
    '''舆情关键词搜索结果解析''' 
    def get_totalpages(self,total_pq):
        '''获取关键词搜索结果总页数'''
        data = total_pq("div.W_pages").find('li')
        total_page = len(data)
        if total_page == 0:   #此时没有页数列表，即只有一页
            return 1
        else:
            return total_page

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
    total_pq = pq(unicode(s)) 
    print analyzer.get_totalpages(total_pq)
       
