# -*- coding:utf-8 -*-
"""
File Name : 'send2mq.py'.py 
Description: 直连交换机来实现，原始url直接放入url队列中，数据出错的话，放入failed_url队列中
Author: 'wanglongzhen' 
Date: '2016/7/26' '10:58'
"""

import pika
import sys
import logging
import os
import ConfigParser


import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read('db.conf')
host = conf.get('mq', 'host')
port = conf.get('mq', 'port')
user = conf.get('mq', 'user')
passwd = conf.get('mq', 'passwd')
queue_name = conf.get('mq', 'queue_name')

# 消息队列初始化
credentials = pika.PlainCredentials(user, passwd)
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host, int(port), '/', credentials))

channel = connection.channel()

channel.exchange_declare(exchange='topic_logs',
                         type='topic')
ary = ["kern.critical", "A critical kernel error"]
routing_key = ary[1] if len(ary) > 1 else 'anonymous.info'
message = ' '.join(ary[2:]) or 'Hello World!'
channel.basic_publish(exchange='topic_logs',
                      routing_key=routing_key,
                      body=message)
print " [x] Sent %r:%r" % (routing_key, message)
connection.close()