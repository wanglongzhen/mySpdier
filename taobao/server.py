# -*- coding:utf-8 -*-
"""
File Name : 'server'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/5' '19:43'
"""

import json


if __name__ == '__main__':
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 8001))
    sock.listen(5)
    while True:
        connection,address = sock.accept()
        try:
            connection.settimeout(5)
            buf = connection.recv(1024)
            if buf == '1':
                connection.send('welcome to server!')
            else:
                print buf
                json_data = json.loads(buf)
                for item in json_data:
                    print item
                    print json_data[item]

                connection.send('please go out!')
        except socket.timeout:
            print 'time out'
        connection.close()