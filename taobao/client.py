# -*- coding:utf-8 -*-
"""
File Name : 'client'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/5' '19:43'
"""

if __name__ == '__main__':
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8001))
    import time
    time.sleep(2)
    json_data = '{"message":1,"result":1, "info": {"user":13649258904, "password":728672}}'
    sock.send(json_data)
    print sock.recv(1024)
    sock.close()