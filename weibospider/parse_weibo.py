# _*_coding:utf-8 _*_
from pyquery import PyQuery as pq
import sys
reload(sys)
reload(sys)
sys.setdefaultencoding("utf-8")
s = """<ul class="WB_row_line WB_row_r4 clearfix S_line2">
                                    <li>
                                                    <a href="javascript:void(0);" class="S_txt2" action-type="fl_pop" action-data="mid=3922827503327692&amp;from=p_profile_pc_05" suda-uatrack="key=profile_feed&amp;value=popularize_host"><span class="pos"><span class="line S_line1">
                                                                                    <i class="S_txt2" title="此条微博已经被阅读581次">阅读 581</i>&nbsp;
                                                                                                                            推广                                                                            </span></span>
                            </a>
                        			        </li>
                                                    <li>
                        <a action-data="allowForward=1&amp;url=http://weibo.com/2728266823/D9zQydXGs&amp;mid=3922827503327692&amp;name=东哥byr&amp;uid=2728266823&amp;domain=donggebyr&amp;pid=a29e0c47jw1ez8bmhpsmtj20c30dvq4d" action-type="fl_forward" action-history="rec=1" href="javascript:void(0);" class="S_txt2" suda-uatrack="key=profile_feed&amp;value=transfer"><span class="pos"><span class="line S_line1" node-type="forward_btn_text"><span><em class="W_ficon ficon_forward S_ficon"></em><em>转发</em></span></span></span></a>
                        <span class="arrow"><span class="W_arrow_bor W_arrow_bor_t"><i class="S_line1"></i><em class="S_bg1_br"></em></span></span>
                    </li>
                                <li>
                                            <a href="javascript:void(0);" class="S_txt2" action-type="fl_comment" action-data="ouid=2728266823&amp;location=profile&amp;comment_type=0" suda-uatrack="key=profile_feed&amp;value=comment:3922827503327692"><span class="pos"><span class="line S_line1" node-type="comment_btn_text"><span><em class="W_ficon ficon_repeat S_ficon"></em><em>5</em></span></span></span></a>
                                        <span class="arrow"><span class="W_arrow_bor W_arrow_bor_t"><i class="S_line1"></i><em class="S_bg1_br"></em></span></span>
                </li>
                <li>
                    <a href="javascript:void(0);" class="S_txt2" action-type="fl_like" action-data="version=mini&amp;qid=heart&amp;mid=3922827503327692&amp;loc=profile" title="赞" suda-uatrack="key=profile_feed&amp;value=like"><span class="pos"><span class="line S_line1"><span node-type="like_status"><i class="W_icon icon_praised_b"></i> <em>4</em></span></span></span></a>
                    <span class="arrow"><span class="W_arrow_bor W_arrow_bor_t"><i class="S_line1"></i><em class="S_bg1_br"></em></span></span>
                </li>
            </ul>"""                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
total_pq = pq(unicode(s))
data = total_pq('ul.WB_row_line')

if not data:
    print "null"
else:
    s = data.find('li').eq(2).find('em').eq(1).text()
    if not s or s == '转发':
        print "no!!!"
    else:
        print s

    s = data.find('li').eq(3).find('em').eq(0).text()
    #s = data.find('li').eq(0)
    print s
    print "not null"
