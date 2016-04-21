# _*_ coding:utf-8 _*_
import re
from pyquery import PyQuery as pq
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
s = '''<p class="comment_txt" node-type="feed_list_content" nick-name="魏驾来魏">
        　　自1999年HBO纪录片报道以来，美国人Jonah Falcon便以其“世界最长阴 茎”闻名全球。Falcon在旧金山<em class="red">机场</em>准备登记时被怀疑藏有<em class="red">炸弹</em>，搜身后证实实为Falcon的下体
                </p>'''
total_pq = pq(unicode(s))
p = total_pq("p.comment_txt").text()
print p
