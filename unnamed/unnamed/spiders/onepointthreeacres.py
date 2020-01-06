# -*- coding: utf-8 -*-
import scrapy
from private import API_KEY
from pushbullet import Pushbullet
import pickle
import time
from pydispatch import dispatcher
from scrapy import signals
from unnamed.items import UnnamedItem

class OnePointThreeAcres(scrapy.Spider):
    name = "1p3a"

    def __init__(self):
        dispatcher.connect(self.on_close, signals.spider_closed)

    def on_close(self, spider):
        f = open("hashes", "w")
        pickle.dump(self.set_, f)
        f.close()

    def start_requests(self):
        urls = [
                 'https://www.1point3acres.com/bbs/forum-28-1.html',
                 'https://www.1point3acres.com/bbs/forum-29-1.html',
                 'https://www.1point3acres.com/bbs/forum-41-1.html',
                 'https://www.1point3acres.com/bbs/forum-47-1.html',
                 'https://www.1point3acres.com/bbs/forum-99-1.html',
                 'https://www.1point3acres.com/bbs/forum-189-1.html',
                 'https://www.1point3acres.com/bbs/forum-78-1.html',
                 #'https://www.1point3acres.com/bbs/forum-80-1.html',
                 #'https://www.1point3acres.com/bbs/forum-142-1.html',
                 #'https://www.1point3acres.com/bbs/forum-70-1.html',
                 #'https://www.1point3acres.com/bbs/forum-224-1.html'
                ]

        self.dict_ctr = {}
        for url in urls:
            self.dict_ctr[url] = 0


        try:
            f = open("hashes", "r")
            self.set_ = pickle.load(f)
            f.close()
        except (IOError, EOFError):
            self.set_ = set()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        table = response.css("#threadlisttableid")
        tbody = table[0].select("tbody")
        filter_func = lambda x:x.xpath("@id").extract()[0].startswith("normalthread")
        threads = filter(filter_func, tbody)

        msg_to_send = ""
        for thread in threads:
            title = thread.css("tr > th > a.s.xst::text").extract()[0]
            url ="https://www.1point3acres.com/bbs/" + thread.css("tr > th > a.s.xst").xpath("@href").extract()[0]
            try:
                time_publish = thread.css("tr > td:nth-child(3) > em > span::text").extract()[0]
            except IndexError:
                time_publish = thread.css("tr > td:nth-child(3) > em > span > span::text").extract()[0]

            try:
                time_lastrsp = thread.css("tr > td:nth-child(5) > em > a::text").extract()[0]
            except IndexError:
                time_lastrsp = thread.css("tr > td:nth-child(5) > em > a > span::text").extract()[0]

            try:
                tag = thread.css("tr > th > em > a::text").extract()[0]
            except IndexError:
                tag = ""

            hash_ = hash(title+url+time_publish)
            if hash_ not in self.set_:
                self.set_.add(hash_)
                msg_to_send += ("[%s]%s\n"%(tag,title) + "%s %s %s\n\n" % (url, time_publish, time_lastrsp)) 
                self.dict_ctr[response.request.url] += 1
                if self.dict_ctr[response.request.url] == 2:
                    break
        item = UnnamedItem()
        item["name"] =  OnePointThreeAcres.name
        item["res"] =  msg_to_send
        return item

