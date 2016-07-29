# -*- coding:utf-8 -*-
"""
File Name : 'spider_baixing'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/7/18' '16:17'
"""


import sys
import requests
import selenium
from bs4 import BeautifulSoup as bs
import execjs
import traceback
import re
import urlparse
import time

import ConfigParser
import pymssql

import os
import GET_Proxies
import random
import distinct


reload(sys)
sys.setdefaultencoding('utf-8')

class GetConn(object):
    """
    获取数据库连接
    """
    def get_db_conn(self, cfg_page = 'db.conf'):
        # 初始化配置文件
        conf = ConfigParser.ConfigParser()
        conf.read(cfg_page)
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
    def __init__(self):
        self._host = 'http://shanghai.baixing.com'
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36',
        }

        self._s = requests.session()

        conn1 = GetConn()
        self._conn = conn1.get_db_conn()


        # self._proxies = GET_Proxies.get_proxies(1000)
        self._proxies = []
        print len(self._proxies)
        self.initProxy()
        print len(self._proxies)
        print "success proies", self._proxies

        #redis

        #redis
        self._redis = 'baixing:urls'
        self._pool, self._rd = distinct.redis_init()
        sql = "select url from danbaobaoxian where source = 3"
        cursor = self._conn.cursor()
        cursor.execute(sql)

        sql_result = cursor.fetchmany(1000)
        count = 0
        while sql_result:
            for item in sql_result:
                for url in item:
                    count = count + 1
                    distinct.check_repeate(self._rd, url, self._redis)

            sql_result = cursor.fetchmany()

        cursor.close()

        self._failed_detail_urls = []
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):

        path = 'failed_urls/failedurls' + time.strftime('%Y%m%d-%H%M', time.localtime())
        self.writeFailedDetailUrl(path)

        self._conn.close()
        pass

    def initProxy(self):

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
                '124.250.29.120:80',
                '218.205.76.175:80',
                '120.52.73.31:86',
                '120.52.73.105:80',
                '52.37.83.211:80',
                '52.64.137.194:8080',
                '120.52.73.27:8080',
                '114.215.243.240:80',
                '121.199.38.82:80',
                '120.52.73.30:80',
                '120.240.4.30:8080',
                '111.13.109.53:80',
                '120.52.73.137:8080',
                '120.52.72.54:80',
                '124.250.29.71:80',
                '183.91.33.43:8080',
                '183.91.33.74:8080']

        with open('proxy/proxies') as f:
            list = []
            for line in f.readlines() :
                list.append(line.replace('\n', ''))

        self._proxies = list

    def getNextProxy(self):
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

        print "Write"
        if os.path.exists(os.path.dirname(path)):

            f = open(path, 'w')
        else:
            os.makedirs(os.path.dirname(path))
            f = open(path, 'w')

        while True:
            for url in self._failed_detail_urls:
                f.write(url + "\n")

            # if not self._q.empty():
            #     value = self._q.get(False)
            #     print "value: ", value
            #     f.write(value + "\n")
            # else:
            #     break

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

        # for city, city_url in uniq_citys:
        #     print city.encode('utf-8')
        #     print city_url

        return uniq_citys

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
                r = self._s.get(url, proxies = proxies, headers = self._headers)
                # r = self._s.get(url, headers = self._headers)
                soup = bs(r.text, 'html.parser')

                #取正文数据中的url
                content_urls = self.getContent(soup)
                if len(content_urls) == 0:
                    raise ("Content_urls length is 0")

                print content_urls

            except Exception, e:
                # self._proxies.remove(strproxy)
                self.removeProxy(strproxy)
                continue
                print traceback.print_exc()

            #可以用消息队列来处理，把列表推送到消息队列中
            for detail_url in content_urls:
                try:
                    data = self.getDetailContentByUrl(detail_url)
                    if len(data) != 0 : self.writeDB(data)
                except Exception, e:
                    print traceback.print_exc()
                    continue

                # time.sleep(1)

            #分页
            cur_page_num, max_page_num, next_page_url = self.getCurPageNum(host, soup)
            print cur_page_num, max_page_num, next_page_url


            if cur_page_num == max_page_num:
                return

            url = next_page_url

    def getDetailContentByUrl(self, detail_content_url):
        """
        根据详情页url获得贷款中介的详情信息
        :param detail_content_url: 贷款中介的详情url
        :return: 返回贷款中介信息的字典
        """

        data = {}

        proxy, proxies = self.getNextProxy()
        # print "time: ", time.strftime('%Y-%m-%d:%H-%M-%S'), proxies
        # print detail_content_url

        #去重
        result = 1
        url = detail_content_url
        m = re.match('(.*html)\?.*', url)
        if m:
            url = m.group(1)
        result = distinct.check_repeate(self._rd, url, self._redis)
        if result == 0: return data

        try:
            r = self._s.get(detail_content_url, proxies = proxies, headers = self._headers)
        except Exception, e:
            # self._proxies.remove()
            self.removeProxy(proxy)
            self.putFailedDetailUrl(detail_content_url)
            # print traceback.print_exc()
            return data


        soup = bs(r.text, 'html.parser')

        try:

            data['title'] = soup.find('div', class_ = 'viewad-title').find('h1').get_text().encode('utf-8')
            data['post_time'] = soup.find('div', class_ = 'viewad-actions').find('span', attrs = {'data-toggle' : 'tooltip'}).get_text().encode('utf-8')

            service_feature_tag = soup.find('div', class_ = 'viewad-meta2-item fuwu-content')
            if service_feature_tag == None:
                service_feature_tag = soup.find('div', class_ = 'viewad-meta2-item')
            else:
                service_feature_tag = service_feature_tag.find('div')
            data['service_feature'] = service_feature_tag.get_text().encode('utf-8')

            data['phone_number'] = soup.find('div', class_ = 'modal modal-load disable-setpos hide').find('div', class_ = 'infoPart').find('p', id = 'mobileNumber').get_text().encode('utf-8')
            data['service_provided'] = soup.find('div', class_ = 'viewad-text').get_text().encode('utf-8')
            data['source'] = '3'
            data['url_hash'] = hash(detail_content_url)
            data['url'] = detail_content_url

            data['post_time'] = re.sub('\s|\xc2\xa0', '', data['post_time'])
        except Exception, e:
            # print traceback.print_exc()
            # self._proxies.remove()
            self.putFailedDetailUrl(detail_content_url)
            self.removeProxy(proxy)

        return data

    def writeDB(self, data):
        """
        写数据
        :param sql:
        :return:
        """

        # print data
        cursor = self._conn.cursor()
        insert_sql = 'insert into danbaobaoxian(title, post_time, service_feature, phone_number, service_provided, source, url_hash, url) values('\
                     + "'" + data['title'] + "', '" + data['post_time'] + "', '" + data['service_feature'] + "', '" + data['phone_number'] \
                     + "', '" + data['service_provided'] + "', " + data['source'] + ", " + str(data['url_hash']) + ", '" + data['url'] + "'" + ')'

        try:
            cursor.execute(insert_sql.encode('utf-8'))
        except Exception, e:
            pass
            # print "Error insert sql", insert_sql.encode('utf-8')
            # print traceback.print_exc()
        finally:
            self._conn.commit()
            cursor.close()


    def getContent(self, soup):
        """
        获取百姓网页面中的正文url信息
        :param soup:页面html
        :return:返回获得的url列表

        """
        content_urls = [content_url.get('href') for item in soup.find_all('ul', class_ = 'list-ad-items') for content_url in item.find_all('a', class_ = 'ad-title')]
        #
        # for content in content_urls:
        #     print content.encode('utf-8')

        return content_urls

    def getNextPageUrl(self, soup):
        """
        根据页面元素，获得下一页的url
        :param soup:
        :return:
        """

        pass


    def getCurPageNum(self, host, soup):
        """
        根据页面底部的分页信息，获取当前分页值和总分页值
        :param soup: 页面html
        :return: 返回当前分页和总的分页数
        """

        cur_page_num = -1
        next_page_num = -1
        next_page_url = None
        max_page_num = -1

        # print "getCurPageNum", cur_page_num, max_page_num

        page_nums = [page_num.get_text() for item in soup.find_all('ul', class_ = 'list-pagination') for page_num in item.find_all('li', class_ = 'active')]
        for num in page_nums:
            cur_page_num = int(num)
            next_page_num = cur_page_num + 1

        page_nums = [(page_num.get_text(), page_num) for item in soup.find_all('ul', class_ = 'list-pagination') for page_num in item.find_all('li', class_ = '')]
        for num, url in page_nums:
            try:
                page_num = int(num)

                if page_num > max_page_num:
                    max_page_num = page_num
                if next_page_num == page_num:
                    next_page_url =  urlparse.urljoin(host, url.find('a').get('href'))
            except Exception, e:
                page_num = -1
                continue

        print "getCurPageNum", cur_page_num, max_page_num, next_page_url
        return cur_page_num, max_page_num, next_page_url


if __name__ == '__main__':
    spider = BaiXing()

    #获取城市
    city_url = 'http://www.baixing.com/?changeLocation=yes&return=%2F'
    uniq_citys = spider.getCitys(city_url)

    print "start------------------------"
    #抓取贷款中介信息
    for city, city_url in uniq_citys:
        url = city_url + 'jinrongfuwu/?page=1'
        print "start page url ", city.encode('utf-8'), url
        spider.spider(city_url, url)
    # url = 'http://shanghai.baixing.com/jinrongfuwu/?page=1'
    # spider.spider(url)

    print "end---------------------------"