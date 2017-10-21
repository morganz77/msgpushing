# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from spiders.private import API_KEY
from pushbullet import Pushbullet

class UnnamedPipeline(object):
    def __init__(self):
        self.msg = ""
        self.title = ""
        self.pb = Pushbullet(API_KEY)
    def process_item(self, item, spider):
        if not self.title:
            self.title = item['name']
        self.msg += item['res']
        #return item
    def close_spider(self, spider):
        #print self.result
        self.pb.push_note(self.title,  self.msg)
