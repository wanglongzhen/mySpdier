# -*- coding:utf-8 -*-
"""
File Name : 'SocketServer'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/24' '19:37'
"""

# 创建SocketServerTCP服务器：
import SocketServer
from SocketServer import StreamRequestHandler as SRH
from time import ctime
from Spider import MobileSpider

import time
import json
import traceback

host = 'localhost'
port = 9999
addr = (host, port)


class Servers(SRH):
    def handle(self):
        print 'got connection from ', self.client_address
        self.wfile.write('connection %s:%s at %s succeed!' % (host, port, ctime()))
        mobile = None

        while True:
            data = self.request.recv(1024)
            if not data:
                break

            #业务逻辑
            try:
                json_data = json.loads(data)
                method = json_data['method']
                phone_num = json_data['task_no']
                mobile_type = json_data['param']['mobile_type']
                phone_passwd = json_data['param']['password']


                if method == 'login' and mobile == None:
                    print 'mobile is None login method'
                    mobile = MobileSpider(phone_num, phone_passwd)
                    response = mobile.login()
                    response = '{"error_no": 0, "task_no": 18115616158, "message": "登录成功"}'

                    time.sleep(10)
                    self.request.send(response + str(ctime()))
                    print 'send to client'
                elif method == 'login' and mobile != None:
                    print 'mobile is not None login method'

                    time.sleep(5)
                    print 'send to client'
                    self.request.send('send to client' + str(ctime()))
            except Exception, e:
                print e
                print traceback.print_exc()


            print data

            print "RECV from ", self.client_address
            self.request.send("Server response" + str(ctime()))


print 'server is running....'
server = SocketServer.ThreadingTCPServer(addr, Servers)
server.serve_forever()