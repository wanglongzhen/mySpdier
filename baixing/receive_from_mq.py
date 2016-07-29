# -*- coding:utf-8 -*-
"""
File Name : 'receive_from_mq'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/7/26' '14:38'
"""

import pika
import sys
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

result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue

# binding_keys = sys.argv[1:]
binding_keys = ['#', "kern.*", "*.critical", "kern.*", "*.critical"]
if not binding_keys:
    print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_logs',
                       queue=queue_name,
                       routing_key=binding_key)

print ' [*] Waiting for logs. To exit press CTRL+C'

def callback(ch, method, properties, body):
    print " [x] %r:%r" % (method.routing_key, body,)

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)

channel.start_consuming()