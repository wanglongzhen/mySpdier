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
from Spider import UnicomSpider


import ConfigParser
import time
import json
import traceback

import comm_log


class Servers(SRH):
    def __init__(self, request, client_address, server):
        """
        初始化函数
        """

        # self.logger = comm_log(123321)
        # self.logger.info(u'服务端初始化成功')

        SRH.__init__(self, request, client_address, server)


    def handle(self):
        """
        处理客户端发来的请求
        :return:
        """
        print 'got connection from ', self.client_address
        # self.wfile.write('connection %s:%s at %s succeed!' % (self.server.server_address[0], self.server.server_address[1], ctime()))
        mobile = None

        while True:
            data = self.request.recv(1024)
            if not data:
                break

            #业务逻辑
            response = self.spider(data, mobile)
            str_response = json.dumps(response)
            self.request.send(str_response)

    def spider(self, data, mobile):
        """
        开始爬取
        :param data:
        :param mobile:
        :return:
        """
        response = {}

        json_data = self.json_value(data)
        if json_data == None:
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "传入数据格式不是json格式，解析失败"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response

        if  json_data['method'] == 'login' and mobile == None:
            # 1登录联通
            print 'mobile is None login method'
            mobile = UnicomSpider(json_data['task_no'], json_data['param']['password'])
            ret, message = mobile.login()
            if ret == True:
                response['error_no'] = 0
                response['task_no'] = json_data['task_no']
                response['message'] = message
                response['timeout'] = 15
                response['img_flag'] = 0


                str_response = json.dumps(response)
                self.request.send(str_response)

                #2 登录后爬取数据
                print 'mobile Spider detail info'
                mobile.spider_detail()
            else:
                response['error_no'] = 1
                response['task_no'] = json_data['task_no']
                response['message'] = message
                response['timeout'] = 15
                response['img_flag'] = 0

            return response

        elif json_data['method']  == 'login' and mobile != None:
            print 'mobile is not None login method'
            response['error_no'] = 1
            response['task_no'] = json_data['task_no']
            response['message'] = "登录成功，正在下载中"
            response['timeout'] = 15
            response['img_flag'] = 0

            return response

    def json_value(self, json_str):
        """
        解析客户端发送的json串，如果不是json格式的则返回None
        :param json_str:
        :return:
        """
        # 业务逻辑
        json_data = None
        try:
            json_data = json.loads(json_str)
            return json_data
        except Exception, e:
            print e
            print traceback.print_exc()
            # self.logger.info(u'解析数据格式失败，客户端发送数据不是json格式')
        else:
            return None
        finally:
            return json_data


def main(cfg_path = 'db.conf'):
    """
    启动服务端程序，等待客户端调用
    :param cfg_path:
    :return:
    """
    # 初始化配置文件
    conf = ConfigParser.ConfigParser()
    conf.read(cfg_path)
    print conf.sections()

    host = conf.get('server', 'host')
    port = int(conf.get('server', 'port'))
    addr = (host, port)

    print 'server is running....'
    server = SocketServer.ThreadingTCPServer(addr, Servers)
    server.serve_forever()

if __name__ == '__main__':
    main()





