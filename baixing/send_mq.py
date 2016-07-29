# -*- coding:utf-8 -*-
"""
File Name : 'send_mq.py'.py 
Description: 发送消息到消息队列
Author: 'wanglongzhen' 
Date: '2016/5/25' '16:16'
"""

import pika
import sys
import requests
from bs4 import BeautifulSoup as bs
import traceback
import re
import urlparse
import time

import ConfigParser
import pymssql

import os
import random
import distinct

import message_queue
import multiprocessing
import threading

reload(sys)
sys.setdefaultencoding('utf-8')


class GetConn(object):
    """
    获取数据库连接
    """
    def get_db_conn(self, cfg_filename = 'db.conf'):
        # 初始化配置文件
        path_dirname = os.path.dirname(os.path.realpath(__file__))
        cfg_path = path_dirname + "/" + cfg_filename

        conf = ConfigParser.ConfigParser()
        conf.read(cfg_path)
        print conf.sections()

        host = conf.get('tagphonedb', 'host')
        user = conf.get('tagphonedb', 'user')
        passwd = conf.get('tagphonedb', 'passwd')
        database = conf.get('tagphonedb', 'database')

        conn = pymssql.connect(host=host, user=user, password = passwd, database=database, charset='utf8')

        return conn


class BaiXing(object):
    """
    爬取百姓网贷款中介信息，并存储到数据库中
    """
    def __init__(self, mq_name = 'task_queue', redis_name = 'baixing:pagesurls', proxy_filename = 'proxy/proxies'):
        self._host = 'http://shanghai.baixing.com'
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36',
        }

        self.thread_num = 15

        self._s = requests.session()

        conn1 = GetConn()
        self._conn = conn1.get_db_conn()

        #取代理
        self._proxies = []
        print len(self._proxies)
        self.initProxy(proxy_filename)
        print len(self._proxies)
        print "success proies", self._proxies

        #redis
        self._redis = redis_name
        self._pool, self._rd = distinct.redis_init()
        self._failed_detail_urls = []

        self.mq = message_queue.message(mq_name)


    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):

        path = 'failed_urls/failedurls' + time.strftime('%Y%m%d-%H%M', time.localtime())
        self.writeFailedDetailUrl(path)

        self._conn.close()
        distinct.redis_close(self._pool)

        self.mq.message_queue_close()
        pass


    def initProxy(self, proxy_filename = 'proxy/proxies'):
        """
        初始化代理
        :param proxy_filename:从代理文件中获取代理
        :return: 代理的列表
        """
        path_dirname = os.path.dirname(os.path.realpath(__file__))
        proxy_path = path_dirname + "/" + proxy_filename

        list = ['120.52.73.31:84',
                '61.191.27.117:123',
                '122.96.59.105:81',
                '120.52.73.132:8080',
                '120.52.73.140:91',
                '163.153.22.9:8080',
                '120.52.73.29:8080',
                '52.69.20.245:3128',
                '120.52.73.134:8080',
                '123.103.16.18:80',
                '120.52.72.47:9011',
                '120.131.128.211:80',
                '183.91.33.74:92',
                '121.199.38.82:80',
                '120.52.73.30:80',
                '120.240.4.30:8080',
                '111.13.109.53:80',
                '120.52.73.137:8080',
                '120.52.72.54:80',
                '124.250.29.71:80',
                '183.91.33.43:8080',
                '183.91.33.74:8080']

        with open(proxy_path) as f:
            list = []
            for line in f.readlines() :
                list.append(line.replace('\n', ''))

        self._proxies = list

    def getNextProxy(self):
        try:
            proxy = random.choice(self._proxies)
        except Exception, e:
            self.initProxy()
            proxy = random.choice(self._proxies)

        # proxy = '120.52.73.31:84'
        proxies = {
            "http": "http://{proxy}".format(proxy=proxy),
            "https": "https://{proxy}".format(proxy=proxy)
        }

        return proxy, proxies

    def removeProxy(self, proxy):
        self._proxies.remove(proxy)
        if len(proxy) == 0:
            self.initProxy()

    def putFailedDetailUrl(self, url):
        self._failed_detail_urls.append(url)

    def writeFailedDetailUrl(self, path = 'failed_urls/failed_urls'):
        path_dirname = os.path.dirname(os.path.realpath(__file__))
        failed_urls_path = path_dirname + "/" + path

        print "Write"
        if os.path.exists(os.path.dirname(failed_urls_path)):
            f = open(path, 'w')
        else:
            os.makedirs(os.path.dirname(failed_urls_path))
            f = open(path, 'w')

        while True:
            for url in self._failed_detail_urls:
                f.write(url + "\n")

        f.close()

    def getCitys(self, url):

        try:
            strproxy, proxies = self.getNextProxy()
            r = self._s.get(url, proxies = proxies, headers = self._headers)
        except Exception, e:
            self._proxies.remove(strproxy)
            print traceback.print_exc()

        soup = bs(r.text, 'html.parser')

        citys = [(item.get_text(), item.get('href')) for li in soup.find_all('ul', class_ = 'wrapper') for item in li.find_all('a')]
        uniq_citys = set(citys)

        return uniq_citys

    def do(self, urls):

        while(len(urls) > 0):
            tds = []
            for i in range(self.thread_num):
                if len(urls) > 0:
                    city, city_url = urls.pop()
                    url = city_url + 'jinrongfuwu/?page=1'
                    tds.append(threading.Thread(target = self.spider, kwargs = {'host' : city_url, 'url' : url}))
                else:
                    break

            for td in tds:
                td.start()

            for td in tds:
                td.join()


    def spider(self, host, url):
        """
        爬百姓网，任务入口
        :param url: 其实url
        :return:
        """

        if len(self._proxies) <= 0:
            print "proxies is 0"
            return

        next_page_url = url
        while(next_page_url != None):
            try:
                print "time: ", time.strftime('%Y-%m-%d:%H-%M-%S'), next_page_url

                strproxy, proxies = self.getNextProxy()

                begin = time.time()
                r = self._s.get(url, proxies = proxies, headers = self._headers, allow_redirects = False, timeout = 10)
                end = time.time()

                time_out = 'URL %s runs %0.2f seconds, and proxy is : %s' % (next_page_url, (end - begin), strproxy)
                print time_out
                # self.WriteProies(time_out, 'out/timeout_' + str(os.getpid()))

                soup = bs(r.text, 'html.parser')

                # result = distinct.check_repeate(self._rd, url, self._redis)
                result = 1
                if result == 0: pass
                else:
                    #取正文数据中的url
                    content_urls = self.getContent(soup)
                    print content_urls
                    if len(content_urls) == 0:
                        raise ("Content_urls length is 0")
                    else:
                        for item in content_urls:
                            self.mq.send_message(item)

            except Exception, e:
                # self._proxies.remove(strproxy)
                self.removeProxy(strproxy)

                print traceback.print_exc()
                print e
                continue

            if int(end-begin) > 10:
                self.removeProxy(strproxy)
                time_out = "URL %s, proxy %s, timeout : %0.2f " % (next_page_url, strproxy, (end-begin))
                self.WriteProies(time_out, 'out/timeout_' + str(os.getpid()))

            #分页
            cur_page_num, max_page_num, next_page_url = self.getCurPageNum(host, soup, next_page_url)
            if cur_page_num == -1 and max_page_num == -1 :
                continue

            if cur_page_num >= max_page_num:
                return

            url = next_page_url

    def WriteProies(self, data, path = 'out/timeout'):

        if os.path.exists(os.path.dirname(path)):
            f = open(path, 'a')
        else:
            os.makedirs(os.path.dirname(path))
            f = open(path, 'w')

        try:
            f.write(data + "\n")
        except Exception, e:
            pass

        f.close()


    def getContent(self, soup):
        """
        获取百姓网页面中的正文url信息
        :param soup:页面html
        :return:返回获得的url列表

        """
        content_urls = [content_url.get('href') for item in soup.find_all('ul', class_ = 'list-ad-items') for content_url in item.find_all('a', class_ = 'ad-title')]

        return content_urls


    def getCurPageNum(self, host, soup, url):
        """
        根据页面底部的分页信息，获取当前分页值和总分页值
        :param soup: 页面html
        :return: 返回当前分页和总的分页数
        """
        cur_page_num = -1
        next_page_num = -1
        next_page_url = url
        max_page_num = -1

        page_nums = [page_num.get_text() for item in soup.find_all('ul', class_ = 'list-pagination') for page_num in item.find_all('li', class_ = 'active')]
        for num in page_nums:
            cur_page_num = int(num)
            next_page_num = cur_page_num + 1

        page_nums = [(page_num.get_text(), page_num) for item in soup.find_all('ul', class_ = 'list-pagination') for page_num in item.find_all('li', class_ = '')]
        for num, url in page_nums:
            try:
                page_num = int(num)

                if page_num >= max_page_num:
                    max_page_num = page_num
                if next_page_num == page_num:
                    next_page_url =  urlparse.urljoin(host, url.find('a').get('href'))
            except Exception, e:
                page_num = -1
                continue

        print "getCurPageNum and cur_page_num is : %s, max_page_num is %s, next_page_url is %s" % (cur_page_num, max_page_num, next_page_url)

        return cur_page_num, max_page_num, next_page_url



if __name__ == '__main__':
    spider = BaiXing()

    #获取城市
    city_url = 'http://www.baixing.com/?changeLocation=yes&return=%2F'
    uniq_citys = spider.getCitys(city_url)

    print "start------------------------"
    #抓取贷款中介信息
    spider.do(uniq_citys)
    # for city, city_url in uniq_citys:
    #     url = city_url + 'jinrongfuwu/?page=1'
    #     print "start page url ", city.encode('utf-8'), url
    #     spider.spider(city_url, url)


    # url = 'http://shanghai.baixing.com/jinrongfuwu/?page=1'
    # spider.spider(url)

    print "end---------------------------"

