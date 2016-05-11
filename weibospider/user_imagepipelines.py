#-*- coding: utf-8 -*-
import logging
import re
import scrapy
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline

logger = logging.getLogger(__name__)

class UserImagesPipeline(ImagesPipeline):
   
    def file_path(self,request,response=None,info=None):
        p1 = re.compile('uid=(\d*)')
        match1 = p1.search(request.url)
        if(match1):
            return 'full/%s.jpg' % match1.group(1)
        else:
            logger.warning("no matched full head_image_name!!")
            return 'wrong path'

    def thumb_path(self,request,thumb_id,response=None,info=None):
        p1 = re.compile('uid=(\d*)')
        match1 = p1.search(request.url) 
        if(match1):
            return 'thumbs/%s/%s_thumbnail.jpg' % (thumb_id,match1.group(1))
        else:
            logger.warning("no matched thumb_head_image_name!!")
            return 'wrong path'

    def get_media_requests(self,item,info):
        if 'image_urls' in item and item['image_urls']: #item中有image_urls字段且其不为None
            image_url = item['image_urls']
            yield scrapy.Request(image_url)

    def item_completed(self,results,item,info):
        image_paths = [x['path'] for isTrue,x in results if isTrue]
        if not image_paths:
            raise DropItem("Item contains no images")
        return item
