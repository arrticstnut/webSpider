#!/usr/bin/python
# -*- coding:UTF-8 -*-
#

import sys 
reload(sys)
sys.setdefaultencoding('utf-8')

#引入文件
import scrapy
from webSearch.webSearchItems import WebSearchItem
import re
import MySQLdb
import redis

#from scrapy import optional_features
#optional_features.remove('boto')


class SinaSpider(scrapy.Spider):
    #用于区别不同spider
    name="SinaSpider"
    #爬取的地址
    start_urls=[
            "https://www.sina.com.cn/",    #新浪主页
            "https://news.sina.com.cn/",    #新闻
            "http://tech.sina.com.cn/",    #科技
            "http://sports.sina.com.cn/",    #体育
            "https://mil.news.sina.com.cn/",    #军事
            "https://finance.sina.com.cn/",    #财经
            "http://blog.sina.com.cn/",    #博客
            "http://ent.sina.com.cn/", #娱乐
            "http://auto.sina.com.cn/", #汽车
            "https://fashion.sina.com.cn/", #时尚
            "http://edu.sina.com.cn/", #教育
            "http://travel.sina.com.cn/", #旅游
            "http://games.sina.com.cn/", #游戏
            "http://blog.sina.com.cn/lm/history/",
            ]

    #允许访问的域
    allowed_domains = [
            "www.sina.com.cn",    #新浪主页
            "news.sina.com.cn",    #新闻
            "tech.sina.com.cn",    #科技
            "sports.sina.com.cn",    #体育
            "mil.news.sina.com.cn",    #军事
            "finance.sina.com.cn",    #财经
            "blog.sina.com.cn",    #博客
            "ent.sina.com.cn", #娱乐
            "auto.sina.com.cn", #汽车
            "fashion.sina.com.cn", #时尚
            "edu.sina.com.cn", #教育
            "travel.sina.com.cn", #旅游
            "games.sina.com.cn", #游戏
            ]

    #类的初始化，从mysql中去除url，将不在redis中的url存入redis
    def __init__(self):
        #MySQL连接
        #Mysql数据库名和表名
        self.dbName = "webSearch"
        self.tableName = "webPageTable"
        #用于url去重的reids数据库的set名称
        self.urls_seen = "urls_seen"

        #redis连接池
        self.pool = redis.ConnectionPool(host = "127.0.0.1",port = 6379)
        self.conn = MySQLdb.connect(
                host = "127.0.0.1",
                port = 3306,
                user = "root",
                passwd = "123",
                db = self.dbName,
                charset = "utf8")
        self.cursor = self.conn.cursor()

        #以下从数据库中获取已经爬取过的url，并将为存入redis的存入
        #实现增量爬取

        #redis连接
        self.redis = redis.Redis(connection_pool = self.pool)
        #获取已经爬取过的url
        sql = "select url from %s" % self.tableName
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        #将url存入redis去重
        urls_seen = self.urls_seen
        for row in results:
            url = row[0]
            if not self.redis.sismember(urls_seen,url):
                self.redis.sadd(urls_seen,url)

    
    #爬取的方法
    def parse(self,response):
        #调用爬取本页信息的函数爬取本页信息
        yield scrapy.Request(url=response.url,callback=self.parseHome,dont_filter=False)

    #从门户网站开始爬取链接
    def parseHome(self,response):
        try:
            title = ''
            url = ''
            #获得所有的li标签
            liTagList = response.xpath('//li')
            if not liTagList: return
            for liTagNode in liTagList:
                #获得li标签下的a标签
                aTagList = liTagNode.xpath('.//a')
                if not aTagList: continue
                for aTagNode in aTagList:
                    #获得a标签的文字，即title
                    titleList = aTagNode.xpath('./text()').extract()
                    if not titleList: continue
                    title = str(titleList[0]).strip()
                    #获得url链接
                    urlList = aTagNode.xpath('./@href').extract()
                    if not urlList: continue
                    url = urlList[0]
                    #链接去重,只爬取新的链接
                    urls_seen = self.urls_seen
                    if (self.redis.sismember(urls_seen,url)):
                        continue
                    #将新的url插入redis
                    self.redis.sadd(urls_seen,url)
                    yield scrapy.Request(url = url,callback =lambda response,title = title,url = url:self.parseContent(response,title,url))

        except Exception as e:
            print(e)


    #爬取获得的连接的内容
    def parseContent(self,response,title,url):
        #实例一个容器保存爬取的信息
        item = WebSearchItem()

        #如果主页链接没有标题，则到对应网页上找标题
        if(title == ''):
            #获得标题所在的h1标签
            titleList = response.xpath('//h1')
            if not titleList:
                return
            #获得标题的文字
            #可能有多个h1标题，最后一个才是要获取的
            titleTexts = titleList[-1].xpath('./text()').extract()
            if not titleTexts:
                return
            title = str(titleTexts[0]).strip()
        item['title']= title;
        item['url'] = url;
        item['content'] = ''
        content = ''
        #获得所有的p标签
        pTagList=response.xpath('//p')
        if not pTagList:
                return
        for pTagNode in pTagList:
            #获得文字文字内容
            contentList = pTagNode.xpath('./text()').extract()
            if not contentList:continue #ck
            text = contentList[0].strip().lstrip('“').rstrip('”')
            content += text

        item['content'] = content
        yield item
