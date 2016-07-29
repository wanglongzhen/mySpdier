# -*- coding:utf-8 -*-
"""
File Name : 'receive_mq.py'.py 
Description: 接受消息，并处理消息，处理消息后，只有发送验证消息，才能从队列销毁消息内容
Author: 'wanglongzhen' 
Date: '2016/5/25' '17:22'
"""


import pika
import sys
import requests
from bs4 import BeautifulSoup as bs
import re
import time

import ConfigParser
import pymssql

import os
import random
import distinct
import traceback
import message_queue
import multiprocessing
import threading

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
    def __init__(self, mq_name = 'task_queue', redis_name = 'baixing:urls'):
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
        self._redis = redis_name
        self._pool, self._rd = distinct.redis_init()
        sql = "select count(1) cnt from danbaobaoxian where source = 3"
        cursor = self._conn.cursor()
        cursor.execute(sql)
        for item in cursor.fetchall():
            print item
        #
        # sql_result = cursor.fetchmany(1000)
        # count = 0
        # while sql_result:
        #     for item in sql_result:
        #         for url in item:
        #             count = count + 1
        #             distinct.check_repeate(self._rd, url, self._redis)
        #
        #     sql_result = cursor.fetchmany()
        #
        cursor.close()

        self._failed_detail_urls = []
        self._manager = multiprocessing.Manager()
        self._lock = self._manager.Lock()

        self.lock = threading.Lock()


        self.mq = message_queue.message(mq_name, handle_data=self.callback)
        self.mq.receive_message()


    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):

        print "receive service ended..."

        path = 'failed_urls/failedurls' + time.strftime('%Y%m%d-%H%M', time.localtime())
        self.writeFailedDetailUrl(path)

        self._conn.close()
        self.connection.close()

        distinct.redis_close(self._pool)

        self.mq.message_queue_close()

    def callback(self, body):
        print body
        # time.sleep(10)
        print time.strftime('%Y-%m-%d:%H-%M-%S')
        data = self.getDetailContentByUrl(body)
        try:
            self.writeDB(data)
        except Exception, e:
            pass
        return 1

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
        self.lock.acquire()
        try:

            proxy = random.choice(self._proxies)
        except Exception, e:
            self.initProxy()
            proxy = random.choice(self._proxies)

        self.lock.release()

        # proxy = '120.52.73.31:84'
        proxies = {
            "http": "http://{proxy}".format(proxy=proxy),
            "https": "https://{proxy}".format(proxy=proxy)
        }

        return proxy, proxies

    def removeProxy(self, proxy):
        try:

            self._proxies.remove(proxy)
        except Exception, e:
            pass

        if len(proxy) == 0:
            self.initProxy()

    def putFailedDetailUrl(self, url):
        self._failed_detail_urls.append(url)

    def writeFailedDetailUrl(self, path = 'failed_urls/failed_urls'):

        if os.path.exists(os.path.dirname(path)):

            f = open(path, 'w')
        else:
            os.makedirs(os.path.dirname(path))
            f = open(path, 'w')

        while True:
            for url in self._failed_detail_urls:
                f.write(url + "\n")

        f.close()

    def WriteProies(self, data, path = 'out/detail_timeout'):

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


    def getDetailContentByUrl(self, detail_content_url):
        """
        根据详情页url获得贷款中介的详情信息
        :param detail_content_url: 贷款中介的详情url
        :return: 返回贷款中介信息的字典
        """

        data = {}

        proxy, proxies = self.getNextProxy()

        #去重
        result = 1
        url = detail_content_url
        m = re.match('(.*html)\?.*', url)
        if m:
            url = m.group(1)
        result = distinct.check_repeate(self._rd, url, self._redis)
        if result == 0: return data

        try:
            begin = time.time()
            r = self._s.get(detail_content_url, proxies = proxies, headers = self._headers, timeout = 10)
            end = time.time()
            time_out = 'URL %s runs %0.2f seconds, and proxy is : %s' % (detail_content_url, (end - begin), proxy)
            print time_out
            self.WriteProies(time_out, 'out/detail_timeout_' + str(os.getpid()))
            if int(end-begin) > 10:
                self.removeProxy(proxy)
                time_out = "URL %s, proxy %s, timeout : %0.2f " % (detail_content_url, proxy, (end-begin))
                self.WriteProies(time_out, 'out/detail_timeout_' + str(os.getpid()))
        except Exception, e:
            # self._proxies.remove()
            self.removeProxy(proxy)
            self.putFailedDetailUrl(detail_content_url)
            print traceback.print_exc()
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
            print traceback.print_exc()

            self.putFailedDetailUrl(detail_content_url)
            self.removeProxy(proxy)

        return data

    def writeDB(self, data):
        """
        写数据
        :param sql:
        :return:
        """

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


if __name__ == '__main__':

    print "start  get detail info ---------------------------------"
    spider = BaiXing()
    # mq_name = 'task_queue'
    # mq = message_queue.message(mq_name, handle_data=spider.callback)
    # mq.receive_message()

    print "end get detail info -----------------------------------"

