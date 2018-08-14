#!/usr/bin/python
# -*- coding:UTF-8 -*-
#

import sys 
reload(sys)
sys.setdefaultencoding('utf-8')

import MySQLdb

#引入文件
from scrapy.exceptions import DropItem
import json

class WebSearchPipeline(object):
    def __init__(self):
        #打开文件
        #self.file=open('data.json','w')
        self.num = 0

        #打开数据库连接
        self.conn = MySQLdb.connect(
                host = "127.0.0.1",
                port = 3306,
                user = "root",
                passwd = "123",
                db = "webSearch",
                charset = "utf8")
        self.cursor = self.conn.cursor()

    #该方法用于处理数据
    def process_item(self,item,spider):

        #放弃太短或太长的网页
        lengthCont = len(item['content'].decode("utf8"))#转成unicode，得到真实的汉字字数
        if(lengthCont < 100 or lengthCont > 9990):#数据库限值是10000
            return
        #放弃标题太短的网页，因为有可能是一些导航，或博客主页
        lengthTitle = len(item['title'].decode("utf8"))#转成unicode，得到真实的汉字字数
        if(lengthTitle <= 5 or lengthTitle > 490):#数据库限值是500
            return
        #放弃标题太短的网页，因为有可能是一些导航，或博客主页
        lengthUrl = len(item['url'].decode("utf8"))#转成unicode，得到真实的汉字字数
        if(lengthUrl > 490):#数据库限值是500
            return


        #存入文件
        #self.saveToFile(item)

        #存入数据库
        try:
            self.insertIntoDataBase(item)
            self.num += 1
            #每到100条数据就提交一次
            if(self.num > 10):
                self.conn.commit()
                self.num = 0
        except:
            pass

        return item


    def saveToFile(self,item):#保存到文件
        line=json.dumps(dict(item),ensure_ascii=False)+'\n'
        #写入文件
        self.file.write(line)

    def insertIntoDataBase(self,item):#存入数据库
        values = [item['title'],item['url'],item['content']]
        sql = 'insert into webPageTable (title,url,content) VALUES (%s,%s,%s)'
        self.cursor.execute(sql,values)


    #该方法在spider被关闭时调用。
    def close_spider(self,spider):
        # 提交到数据库执行
        self.conn.commit()
        self.conn.close()

