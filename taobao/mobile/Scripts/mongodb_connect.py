# -*- coding:utf-8 -*-

"""
File Name: mongodb_connect.py
Version: 0.1
Description: 用于构建与Mongodb的连接过程

Author: gonghao
Date: 2016/10/19 11:23
"""

import os
import codecs
import ConfigParser
from mongoengine import connect
from models import Status


def config_parse(parse_name="CMCC"):
    """
    根据给定的消息队列的名称，解析配置
    :param parse_name: 配置文件的Sec_name
    :return:
    """
    cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
    cfg_path = os.path.join(cur_script_dir, "db.conf")

    cfg_reader = ConfigParser.ConfigParser()
    sec_name = parse_name
    cfg_reader.readfp(codecs.open(cfg_path, "r", "utf_8"))

    host = str(cfg_reader.get(sec_name, "host"))
    dbname = str(cfg_reader.get(sec_name, "dbname"))
    username = str(cfg_reader.get(sec_name, "username"))
    passwd = str(cfg_reader.get(sec_name, "passwd"))

    return host, dbname, username, passwd


def connect_mongodb():
    host, dbname, username, passwd = config_parse(parse_name="CMCC")
    conn = connect(dbname, host=host, username=username, password=passwd)

    return conn


def get_last_scape_dt(mobile):
    conn = connect_mongodb()
    last_status = Status.objects(mobile=mobile).order_by("-scrape_dt").first()
    conn.close()

    if last_status:
        last_dt = last_status.scrape_dt
        # 返回样例 (u'2016-11-04 17:15:04', u'2016-11', u'201611')
        return last_dt, last_dt[:7], last_dt[:7].replace("-", ""), last_dt[:10] + ' 00:00:00'
    else:
        return None, None, None, None


if __name__ == '__main__':
    print get_last_scape_dt("18260086180")

