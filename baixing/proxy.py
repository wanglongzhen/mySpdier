# -*- coding:utf-8 -*-
"""
File Name : 'proxy'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/7/20' '11:14'
"""

import sys
import ConfigParser
import pymssql
import multiprocessing
import time
import random
import os
from DBUtils.PooledDB import PooledDB
import requests


class GetConn(object):
    """
    获取数据库连接
    """
    def get_db_conn(self, cfg_page = 'db.conf'):
        # 初始化配置文件
        conf = ConfigParser.ConfigParser()
        conf.read(cfg_page)
        print conf.sections()

        host = conf.get('proxydb', 'host')
        user = conf.get('proxydb', 'user')
        passwd = conf.get('proxydb', 'passwd')
        database = conf.get('proxydb', 'database')

        conn = pymssql.connect(host=host, user=user, password = passwd, database=database, charset='utf8')
        # pool = PooledDB(pymssql, 5, port = 3306, host=host, user=user, password = passwd, database=database, charset='utf-8')

        return conn

class Proxy(object):
    def __init__(self):
        print "init"
        conn1 = GetConn()
        self._conn = conn1.get_db_conn()
        # getConn = GetConn()
        # self._pool = getConn.get_db_conn()
        #
        # sql = "select top 10 * from proxy_list  where speed < 100 "
        # print sql
        # conn = self._pool.connection()
        # cur = conn.cursor()
        # cur.execute(sql)

        # for item in self._pool.fetchall():
        #     print item


        self._manager = multiprocessing.Manager()
        self._q = self._manager.Queue()
        self._lock = self._manager.Lock()

    def __enter__(self):
        print "enter"

        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        print "exit"
        self._cursor.close()
        self._conn.close()


    def do(self):
        print('Parent process %s.' % os.getpid())
        p = multiprocessing.Pool()
        getConn = GetConn()
        conn = getConn.get_db_conn()
        cursor = conn.cursor()

        sql = "select ip, port from proxy_list  where speed < 5"
        print sql

        cursor.execute(sql)
        count = 0
        for ip, port in cursor.fetchall():
            count += 1
            proxy = ip + ":" + port
            p.apply_async(check_proxy, args = (count, proxy, self._q, self._lock))

        print('Waiting for all subprocesses done...')
        p.close()
        p.join()

        self.WriteProies()


        print('All subprocesses done.')

    def WriteProies(self, path = 'proxy/proxies'):

        print "Write"
        if os.path.exists(os.path.dirname(path)):

            f = open(path, 'w')
        else:
            os.makedirs(os.path.dirname(path))
            f = open(path, 'w')

        while True:
            if not self._q.empty():
                value = self._q.get(False)
                print "value: ", value
                f.write(value + "\n")
            else:
                break

        f.close()

def check_proxy(count, proxy, q, lock):
    print('Run task %s (%s)...' % (proxy, os.getpid()))
    start = time.time()

    #写数据
    host = 'http://beijing.baixing.com/jinrongfuwu/?page=1'
    print "proxy check begin : ", proxy
    proxies = {
        "http": "http://{proxy}".format(proxy=proxy),
        "https": "https://{proxy}".format(proxy=proxy)
    }

    try:
        r = requests.get(host, proxies=proxies, timeout = 10)
        r.encoding = 'utf-8'

        if r.text.find(u"百姓网") >= 0:
            print "success:", proxy
            lock.acquire()
            q.put(proxy)
            lock.release()
    except Exception as e:
        print "FAILED"

    print "count %s proxy check end : %s" % (count, proxy)


    # time.sleep(random.random())
    end = time.time()
    print('Task %s runs %0.2f seconds' % (proxy, (end - start)))


def checkProxyEx(host, proxies):

    for proxy in proxies:
        print proxy
        proxies = {
            "http": "http://{proxy}".format(proxy=proxy),
            "https": "https://{proxy}".format(proxy=proxy)
        }

        print proxies
        try:
            r = requests.get(host, proxies=proxies)
            r.encoding = 'utf-8'

            if r.text.find(u"百姓网") >= 0:
                print "success:", proxy
                list.append(proxy)
        except Exception as e:
            print "FAILED"
            continue

def main():
    proxy = Proxy()
    proxy.do()



if __name__ == '__main__':

    main()
