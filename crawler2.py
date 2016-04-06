#-*-coding:utf-8-*-
import sys
from twisted.internet import reactor, defer
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy import signals
from spiders.userinfo import WeiboSpider


reload(sys)
sys.setdefaultencoding('utf-8')
def spider_closing(spider):
    reactor.stop()


settings = Settings()

settings.set("ITEM_PIPELINES",{'weibospider.user_imagepipelines.UserImagesPipeline':1,'weibospider.oracle_pipelines.WeibospiderPipeline':300})
crawler = Crawler(WeiboSpider,settings)
crawler.signals.connect(spider_closing,signal = signals.spider_closed)

#crawler.configure()
crawler.crawl(uid = '3217179555')
reactor.run()
