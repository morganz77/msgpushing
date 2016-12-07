# -*- coding: utf-8 -*-
import scrapy
from private import API_KEY
from pushbullet import Pushbullet
import pickle
import time
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

CACHEPATH = "hashes_hn"
NUMPERURL = 10
MINSCORE = 80
class OnePointThreeAcres(scrapy.Spider):
    name = "hn"

    def __init__(self):
        dispatcher.connect(self.on_close, signals.spider_closed)

    def on_close(self, spider):
        f = open(CACHEPATH, "w")
        pickle.dump(self.set_, f)
        f.close()

    def start_requests(self):
        urls = [
                 'https://news.ycombinator.com/'
                ]

        self.dict_ctr = {}
        for url in urls:
            self.dict_ctr[url] = 0
        self.pb = Pushbullet(API_KEY)

        try:
            f = open(CACHEPATH, "r")
            self.set_ = pickle.load(f)
            f.close()
        except (IOError, EOFError):
            self.set_ = set()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        def build_score_dict(lst):
            #return d[id] -> (score, age)
            d = {}
            score_lst = lst.xpath("//*[@class='score']")
            for ele in score_lst:
                id_ = ele.xpath("@id").extract()[0].split("_")[-1]
                score = ele.css("::text")[0].extract()
                d[id_] = score

            age_lst = lst.xpath("//*[@class='age']")
            for ele in age_lst:
                id_ = ele.css("a").xpath("@href").extract()[0].split("=")[-1]
                age = ele.css("a::text").extract()[0]
                #if id_ == "13124584": print id_, age
                if (id_ in d) and (type(d[id_]) != tuple): #2nd condition is for removing dup ids
                    d[id_] = (d[id_], age)
                elif id_ not in d: #some articles do not have score attribute
                    d[id_] = ("0", age)

            return d
                
        trs = response.css("tr")
        score_dict = build_score_dict(response.css("span"))
        filter_func = lambda x: x.xpath("@id").extract() and x.xpath("@id").extract()[0].isdigit()
        threads = filter(filter_func, trs)
        #print threads

        for thread in threads:
            title = thread.css("td:nth-child(3) > a::text").extract()[0]
            url = thread.css("td:nth-child(3) > a").xpath("@href").extract()[0]
            id_ = thread.xpath("@id").extract()[0]
            score = score_dict[id_][0] 
            age = score_dict[id_][1]

            hash_ = hash(title+url+id_+score)
            if int(score.strip().split()[0]) >= MINSCORE and hash_ not in self.set_:
                self.set_.add(hash_)
                #print "%s %s"%(title, id_), "%s %s %s" % (url, score, age) 
                self.pb.push_note("%s %s"%(title, id_), "%s %s %s" % (url, score, age))
                self.dict_ctr[response.request.url] += 1
                if self.dict_ctr[response.request.url] == NUMPERURL:
                    break

        #self.log('Saved file %s' % filename)
