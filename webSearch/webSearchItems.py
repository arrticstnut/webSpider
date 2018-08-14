#!/usr/bin/python
# -*- coding:UTF-8 -*-
#

import sys 
reload(sys)
sys.setdefaultencoding('utf-8')

#引入文件
import scrapy

class WebSearchItem(scrapy.Item):
    #标题
    title = scrapy.Field()
    #url
    url = scrapy.Field()
    #内容
    content = scrapy.Field()


