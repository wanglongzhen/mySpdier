# -*- coding:utf-8 -*-
"""
File Name : 'SocketServer'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/24' '20:32'
"""

from socket import *

host = 'localhost'
port = 9999
bufsize = 1024
addr = (host, port)
client = socket(AF_INET, SOCK_STREAM)
client.connect(addr)
while True:
    # data = raw_input()
    data = '{"method":"login","task_no":18115616158, "param": {"mobile_type":"mobile_type", "password":728672}}'

    if not data or data == 'exit':
        break
    print data
    client.send('%s\r\n' % data)
    data = client.recv(bufsize)
    if not data:
        break
    print data.strip()
client.close()