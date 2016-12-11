# -*- coding:utf-8 -*-

"""
File Name: redis_connect.py
Version: 0.1
Description: 连接Redis

Author: gonghao
Date: 2016/7/13 11:00
"""

import redis
import os
import json
import codecs

import ConfigParser
import functools
try:
    import cPickle as pickle
except ImportError:
    import pickle

import requests
from settings import REDIS_STATUS_TABLE, REDIS_META_TABLE

def config_parse(parse_name="Redis"):
    """
    根据给定的数据库名，解析配置文件中其对应的host，用户名以及密码
    :param parse_name: 数据库名称
    :return: [tuple] - (host, username, passwd)
    """
    cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
    cfg_path = os.path.join(cur_script_dir, "db.conf")

    cfg_reader = ConfigParser.ConfigParser()
    sec_name = parse_name
    cfg_reader.readfp(codecs.open(cfg_path, "r", "utf_8"))

    host = cfg_reader.get(sec_name, "host")
    port = cfg_reader.get(sec_name, "port")
    db_name = cfg_reader.get(sec_name, "db")
    passwd = cfg_reader.get(sec_name, "passwd")

    return host, port, db_name, passwd


class RedisConnect(object):
    """
    连接Redis数据库
    """
    def __init__(self, parse_name):
        self.host, self.port, self.db, self.password = config_parse(parse_name=parse_name)
        self.pool = redis.ConnectionPool(host=self.host,
                                         port=self.port,
                                         db=self.db,
                                         password=self.password)
        self.r = redis.StrictRedis(connection_pool=self.pool)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.disconnect()
        self.r.connection_pool.disconnect()

    def redis_hset(self, task_id, values, table):
        queue = table + task_id
        self.r.set(queue, values)

    def redis_expire(self, task_id, table, expire_time):
        queue = table + task_id
        self.r.expire(queue, expire_time)

    def redis_hget(self, task_id, table):
        queue = table + task_id
        return self.r.get(queue)

    def redis_insert_set(self, value):
        queue = "cmcc_bill_month_web"
        return self.r.sadd(queue, value)


def _redis_hset(task_id, values, table):
    """
    提供接口，保存数据到Redis（数据类型为String）
    :param table: [str] 表名
    :param task_id: [str] 任务ID
    :param values: [dict] 需要保存的数据
    :return:
    """
    with RedisConnect(parse_name="Redis") as rc:
        rc.redis_hset(task_id, values, table)


def _redis_hget(task_id, table):
    """
    提供接口，保存数据到Redis（数据类型为String）
    :param table: [str] 表名
    :param task_id: [str] 任务ID
    :return: 获得的数据
    """
    with RedisConnect(parse_name="Redis") as rc:
        return rc.redis_hget(task_id, table)


def _redis_expire(task_id, table, expire_time=60 * 60 * 24):
    """
    提供接口，设置Redis中指定键值的自动销毁时间
    :param table: [str] 表名
    :param task_id: [str] 任务ID
    :return:
    """
    with RedisConnect(parse_name="Redis") as rc:
        rc.redis_expire(task_id, table, expire_time)

redis_hset_status = functools.partial(_redis_hset, table=REDIS_STATUS_TABLE)
redis_hget_status = functools.partial(_redis_hget, table=REDIS_STATUS_TABLE)
redis_expire_status = functools.partial(_redis_expire, table=REDIS_STATUS_TABLE)

redis_hset_meta = functools.partial(_redis_hset, table=REDIS_META_TABLE)
redis_hget_meta = functools.partial(_redis_hget, table=REDIS_META_TABLE)
redis_expire_meta = functools.partial(_redis_expire, table=REDIS_META_TABLE)


def redis_insert_set(value):
    """
    检查是否已经存储, 返回：0已经有了；1还没有
    :param value: 包含月份的值
    :return:
    """
    with RedisConnect(parse_name="Redis") as rc:
        flag = rc.redis_insert_set(value)

    return flag

if __name__ == '__main__':
    s = requests.session()
    ss = pickle.dumps(s)
    meta = dict(session=ss, password="12111")
    redis_hset_meta("0001", json.dumps(meta))
    redis_expire_meta("0001")
    meta = json.loads(redis_hget_meta("0001"))

    print redis_insert_set(1)

