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

class weibocontent_analyzer:
    '''预警人员微博内容解析''' 

    def get_weibo_relative_args(self,total_pq):
        '''获取微博相关信息参数:转发数,评论数,点赞数'''
        ul_datas = total_pq('ul.WB_row_line')
        (repost_nums, comment_nums, like_nums) = ([], [], [])
        if ul_datas:
            for ul_data in ul_datas:
                ul_data = pq(ul_data)
                if len(ul_data.find('li')) == 4: #不是'好友圈'微博内容
                    #解析转发数
                    repost_info = ul_data.find('li').eq(1).find('em').eq(1).text()
                    if not repost_info or repost_info == '转发': #若解析出的不是数字,而是"转发",则表示没有转发数
                        repost_nums.append(0)
                    else:
                        repost_nums.append(repost_info)
                     
                    #解析评论数
                    comment_info = ul_data.find('li').eq(2).find('em').eq(1).text()
                    if not comment_info or comment_info == '评论': #若解析出的不是数字,而是"评论",则表示没有评论数
                        comment_nums.append(0)
                    else:
                        comment_nums.append(comment_info)

                    #解析点赞数
                    like_info = ul_data.find('li').eq(3).find('em').eq(0).text()
                    if not like_info or like_info == '赞': #若解析出的不是数字,而是"赞",则表示没有点赞数
                        like_nums.append(0)
                    else:
                        like_nums.append(like_info)
                else:  #属于'好友圈'微博内容,此时len(ul_data.find('li')) = 3
                    #解析转发数:'好友圈'微博内容没有转发属性,直接赋值0
                    repost_nums.append(0)
                     
                    #解析评论数
                    comment_info = ul_data.find('li').eq(1).find('em').eq(1).text()
                    if not comment_info or comment_info == '评论': #若解析出的不是数字,而是"评论",则表示没有评论数
                        comment_nums.append(0)
                    else:
                        comment_nums.append(comment_info)

                    #解析点赞数
                    like_info = ul_data.find('li').eq(2).find('em').eq(0).text()
                    if not like_info or like_info == '赞': #若解析出的不是数字,而是"赞",则表示没有点赞数
                        like_nums.append(0)
                    else:
                        like_nums.append(like_info)

        else:
            logger.warning("no matched weibo_relative_args!!")    

        return repost_nums,comment_nums,like_nums

if __name__ == "__main__":
    test = weibocontent_analyzer()
