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
from mobileSpider import MobileSpider

import ConfigParser
import time
import json
import traceback

import urllib
import urllib2

import comm_log


class Servers(SRH):
    def __init__(self, request, client_address, server):
        """
        初始化函数
        """

        log_name = str(time.time()).replace(".", "0")
        self.logger = comm_log.comm_log(log_name)
        self.logger.info(u'服务端初始化成功.等待客户端发送请求！')
        self.mobile = None

        SRH.__init__(self, request, client_address, server)


    def handle(self):
        """
        处理客户端发来的请求
        :return:
        """
        print 'got connection from ', self.client_address
        self.logger.info(u'客户端连接请求' + str(self.client_address))
        # self.wfile.write('connection %s:%s at %s succeed!' % (self.server.server_address[0], self.server.server_address[1], ctime()))
        #第一次建立连接，初始化一个空的对象

        while True:
            flag = True
            recv_data = self.request.recv(1024)
            self.logger.info(u'客户端' + str(self.client_address) + u' 接收到的数据：')
            self.logger.info(recv_data)
            data = self.json_value(recv_data)
            ret, flag = self.spider(data)
            response = json.dumps(ret)
            # print recv_data
            # time.sleep(20)
            # response = "ddd"

            self.request.send(response)
            self.logger.info(u'客户端' + str(self.client_address) + u' 发送的数据：' + response)

            #如果返回FALSE，则说明交互结束，退出循环
            #如果返回True，则交互正常，继续循环
            if flag == False:
                self.logger.info(u'客户端' + str(self.client_address) + u' 完成交互退出循环')
                break
            else:
                self.logger.info(u'客户端' + str(self.client_address) + u' 等待下一次和客户端交互')
                continue


    def spider(self, data):
        """
        爬取交互的处理逻辑
        :param data:
        :param mobile:
        :return:
        """

        self.logger.info(u'spider 函数开始爬去过程， 参数：')
        self.logger.info(data)

        param = self.get_value_by_data(data, 'param')
        if param == None:
            response = {}
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "传入数据格式不是json格式，解析失败"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True

        # mobile_type = self.get_value_by_data(param, 'mobile_type')
        mobile_type = ''
        try:
            ret, mobile_type = self.get_mobile_type(self.get_value_by_data(data, 'task_no'))
        except:
            print('调用apistore接口判断电话号码运行商错误')
            self.logger.info(u'客户端' + str(self.client_address) + u' 调用apistore接口判断电话号码运行商错误')
            response = {}
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = mobile_type
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True

        self.logger.info(u'客户端' + str(self.client_address) + u' 获取运营商的类型' + mobile_type)
        data['param']['mobile_type'] = mobile_type

        if mobile_type == 'mobile':
            return self.mobile_spider(data)
        elif mobile_type == 'unicom':
            return self.unicom_spider(data)
        elif mobile_type == None:
            response = {}
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "需要传入手机号的mobile_type值"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True
        else:
            #处理其他情况
            pass

    def get_value_by_data(self, data, key):
        """
        从json数据中取出key的值value，如果没有则返回None
        :param data:
        :param key:
        :return:
        """

        value = None
        try:
            value = data[key]
        except Exception, e:
            pass

        return value

    def mobile_spider(self, data):
        """
        移动开始爬取
        :param data:
        :param mobile:
        :return:
        """

        response = {}
        if data == None:
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "传入数据格式不是json格式，解析失败"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True

        method = self.get_value_by_data(data, 'method')
        task_no = self.get_value_by_data(data, 'task_no')
        param = self.get_value_by_data(data, 'param')

        if param == None:
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "param参数不存在，json格式错误"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True

        passwd = self.get_value_by_data(param, 'password')

        if method == 'login' and self.mobile == None:
            # 1登录触发验证码
            print 'mobile is None login method'
            mobile = MobileSpider(task_no, passwd)
            ret, message = mobile.login()
            if ret == True:
                response['error_no'] = 0
                response['task_no'] = task_no
                response['message'] = message
                response['timeout'] = 10

                str_response = json.dumps(response)
                self.request.send(str_response)

                # 等待第一次验证码
                while True:
                    sms_data = self.request.recv(1024)
                    json_sms_data = self.json_value(sms_data)
                    sms_param = self.get_value_by_data(json_sms_data, 'param')
                    sms_passwd = self.get_value_by_data(sms_param, 'sms_pwd')
                    ret, message = mobile.login_first_sms(sms_passwd)

                    if ret == False:
                        response['error_no'] = 1
                        response['task_no'] = task_no
                        response['message'] = message
                        response['timeout'] = 10
                        str_response = json.dumps(response)
                        self.request.send(str_response)
                    elif ret == True:
                        response['error_no'] = 0
                        response['task_no'] = task_no
                        response['message'] = message
                        response['timeout'] = 70
                        str_response = json.dumps(response)
                        self.request.send(str_response)
                        break

                # 等待第二次短信验证码
                while True:
                    sms_data = self.request.recv(1024)
                    json_sms_data = self.json_value(sms_data)
                    sms_param = self.get_value_by_data(json_sms_data, 'param')
                    sms_passwd = self.get_value_by_data(sms_param, 'sms_pwd')
                    ret, message = mobile.login_sec_sms(sms_passwd)

                    if ret == False:
                        response['error_no'] = 0
                        response['task_no'] = task_no
                        response['message'] = message
                        response['timeout'] = 10
                        str_response = json.dumps(response)
                        self.request.send(str_response)
                    elif ret == True:
                        response['error_no'] = 0
                        response['task_no'] = task_no
                        response['message'] = message
                        response['timeout'] = 10
                        str_response = json.dumps(response)
                        self.request.send(str_response)

            else:
                response['error_no'] = 1
                response['task_no'] = task_no
                response['message'] = message
                response['timeout'] = 10

            return False, response


    def unicom_spider(self, data):
        """
        循环处理服务端和客户端的数据，直到结束
        :param data:
        :param mobile:
        :return:
        """
        self.logger.info(u'客户端' + str(self.client_address) + u' 调用 unicom_spider')
        response = {}
        if data == None:
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "传入数据格式不是json格式，解析失败"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True

        method = self.get_value_by_data(data, 'method')
        task_no = self.get_value_by_data(data, 'task_no')
        param = self.get_value_by_data(data, 'param')

        if param == None:
            response['error_no'] = 2
            response['task_no'] = 0
            response['message'] = "param参数不存在，json格式错误"
            response['timeout'] = 15
            response['img_flag'] = 0
            return response, True

        passwd = self.get_value_by_data(param, 'password')
        img_sms = self.get_value_by_data(param, 'img_sms')

        #有图片密码
        if data['method'] == 'login' and img_sms != None:
            # 1登录联通
            print 'login method'
            self.logger.info(u'客户端' + str(self.client_address) + u' 登录联通，有图片验证码')
            # mobile = UnicomSpider(task_no, passwd)
            ret, message = self.mobile.login(img_sms)
            if ret == 0:
                response['error_no'] = 0
                response['task_no'] = data['task_no']
                response['message'] = message
                response['timeout'] = 15
                response['img_flag'] = 0

                str_response = json.dumps(response)
                self.request.send(str_response)

                # 2 登录后爬取数据
                print 'mobile Spider detail info'
                self.logger.info(u'客户端' + str(self.client_address) + u' 登录联通成功，开始爬取数据')
                self.mobile.spider_detail()

                return response, False
            elif ret == 1:
                response['error_no'] = 1
                response['task_no'] = data['task_no']
                response['message'] = '需要输入图片验证码'
                response['timeout'] = 15
                response['img_flag'] = 1
                response['img_data'] = message

                return response, True
            else:
                response['error_no'] = 1
                response['task_no'] = task_no
                response['message'] = message
                response['timeout'] = 15
                response['img_flag'] = 0

            return response, True

        if data['method'] == 'login' and self.mobile == None:
            # 1登录联通
            print 'mobile is None login method'
            self.logger.info(u'客户端' + str(self.client_address) + u' 登录联通，没有图片验证码')
            self.mobile = UnicomSpider(task_no, passwd)
            ret, message = self.mobile.login()
            if ret == 0:
                response['error_no'] = 0
                response['task_no'] = data['task_no']
                response['message'] = message
                response['timeout'] = 15
                response['img_flag'] = 0

                str_response = json.dumps(response)
                self.request.send(str_response)

                # 2 登录后爬取数据
                print 'mobile Spider detail info'
                self.logger.info(u'客户端' + str(self.client_address) + u' 登录成功，开始爬取数据')
                self.mobile.spider_detail()

                return response, False
            elif ret == 1:
                response['error_no'] = 1
                response['task_no'] = data['task_no']
                response['message'] = '需要输入图片验证码'
                response['timeout'] = 15
                response['img_flag'] = 1
                response['img_data'] = message

                return response, True
            else:
                response['error_no'] = 1
                response['task_no'] = task_no
                response['message'] = message
                response['timeout'] = 15
                response['img_flag'] = 0

            return response, True

        elif method == 'login' and self.mobile != None:
            print 'mobile is not None login method'
            self.logger.info(u'客户端' + str(self.client_address) + u' 登录成功，正在爬取中')
            response['error_no'] = 1
            response['task_no'] = task_no
            response['message'] = "登录成功，正在下载中"
            response['timeout'] = 15
            response['img_flag'] = 0

            return response, True

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

    def json_string(self, json):
        """
        json对象转换为json字符串，失败返回None
        :param json:
        :return:
        """
        json_str = None
        try:
            json_str = json.dumps(json)
            return json_str
        except Exception, e:
            print e
            print traceback.print_exc()
        else:
            return None
        finally:
            return json_str

    def get_mobile_type(self, phone, cfg_path = 'db.conf'):
        conf = ConfigParser.ConfigParser()
        conf.read(cfg_path)
        apikey = conf.get('apikey', 'apikey')

        url = 'http://apis.baidu.com/apistore/mobilenumber/mobilenumber?phone=' + str(phone)
        req = urllib2.Request(url)
        req.add_header("apikey", "668786c7da22ae7e7e90607112a5858a")
        resp = urllib2.urlopen(req)
        content = resp.read()

        json_content = json.loads(content)
        while (json_content['errNum'] != 0):
            resp = urllib2.urlopen(req)
            content = resp.read()
            json_content = json.loads(content)
            time.sleep(2)

        if (content):
            print(content)
            json_content = json.loads(content)

            if json_content['errNum'] == 0:
                mobile_type = json_content['retData']['supplier']
                if mobile_type == u'移动':
                    return 0, 'mobile'
                elif mobile_type == u'联通':
                    return 0, 'unicom'
                elif mobile_type == u'电信':
                    return 0, 'telecom'
                else:
                    return 1, '类型不对'
            else:
                return 1, json_content['retMsg']

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
    # host = 'localhost'
    port = int(conf.get('server', 'port'))
    addr = (host, port)

    print 'server is running....'
    server = SocketServer.ThreadingTCPServer(addr, Servers)
    server.serve_forever()

if __name__ == '__main__':
    main()
