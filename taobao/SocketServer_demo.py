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

                mobile = None
                if method == 'login':
                    mobile = MobileSpider(phone_num, phone_passwd)
                    response = mobile.login()
                    response = '{"error_no": 0, "task_no": 18115616158, "message": "登录成功"}'

                    time.sleep(1000)
                    self.request.send(response)
            except Exception, e:
                print e
                print traceback.print_exc()


            print data
            mobile.login_first_sms()

            print "RECV from ", self.client_address
            self.request.send("Server response")


print 'server is running....'
server = SocketServer.ThreadingTCPServer(addr, Servers)
server.serve_forever()