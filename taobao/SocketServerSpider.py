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
from mobile.Scripts.mobile_shop_spider import MobileShopSpider


import ConfigParser
import time
import json
import traceback

import urllib
import urllib2

import comm_log
import unicom
import os
import datetime
import codecs
import platform


class Servers(SRH):
    def __init__(self, request, client_address, server):
        """
        初始化函数
        """

        log_name = str(time.time()).replace(".", "0")
        # self.logger = comm_log.comm_log(log_name)
        self.logger = self.init_log(log_name)
        self.logger.info(u'服务端初始化成功.等待客户端发送请求！')
        self.mobile = None

        SRH.__init__(self, request, client_address, server)


    def init_log(self, logname, conf = './db.conf'):
        #读取日志的路径
        cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
        cfg_path = os.path.join(cur_script_dir, conf)
        cfg_reder = ConfigParser.ConfigParser()
        cfg_reder.readfp(codecs.open(cfg_path, "r", "utf_8"))

        today = datetime.date.today().strftime('%Y%m%d')

        self._SECNAME = "LOGPATH"
        if platform.platform().find("windows") != -1 or platform.platform().find("Windows") != -1:
            self._OPTNAME = "WINDOWS_LOGDIR"
        else:
            self._OPTNAME = "LINUX_LOGDIR"
        self._LOGROOT = cfg_reder.get(self._SECNAME, self._OPTNAME)

        #创建日志文件的路径
        log_path = os.path.join(self._LOGROOT, today)
        if not os.path.isdir(log_path):
            os.makedirs(log_path)

        self.logger = comm_log.comm_log(logname, logpath=log_path)

        self.imgroot = os.path.join(self._LOGROOT, 'img')
        # 如果目录不存在，则创建一个目录
        if not os.path.isdir(self.imgroot):
            os.makedirs(self.imgroot)

        return self.logger

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
            # return self.mobile_spider(data)
            return self.mobile_spider_new(data)
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
            self.logger.info(u'json字符串解析失败')
            self.logger.info(traceback.format_exc())


        return value


    def mobile_spider_new(self, data):
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
            task_id = "cmcc_web_{:13.0f}".format(time.time() * 1000)
            ms_spider_1 = MobileShopSpider(task_id=task_id, phone=task_no, password=passwd, proc_num=task_no,
                                           step="Login")
            # mobile = MobileSpider(task_no, passwd)
            # ret, message = mobile.login()
            is_success, code = ms_spider_1.login()
            if code == "0001":
                # 触发短信验证码成功 返回前端 登录需要短信验证码
                message = "触发登录短信验证码成功"
            elif code == "1010":
                message = u"fali:移动服务异常:step1:{}:{}".format(code, task_id)
            else:
                # 返回前端 其它错误 (不会发生)
                message = u"fail:其它错误:step1:{}:{}".format(code, task_id)
            if is_success == True:
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
                    ms_spider_2 = MobileShopSpider(task_id=task_id, phone=task_no, password=passwd, proc_num=task_no,
                                                   step="SMS_login")
                    is_success, result_code = ms_spider_2.get_sms_verifycode(sms_passwd)
                    # ret, message = mobile.login_first_sms(sms_passwd)

                    if result_code == "0003":
                        # 登录短信验证码成功 请求发送爬取短信验证码
                        message = u"登录短信验证码校验成功:step2:{}:{}".format(result_code, task_id)
                    elif result_code == "1010":
                        # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）or 请求爬取短信验证码失败
                        message = u"移动服务异常:step2:{}:{}".format(result_code, task_id)
                    elif result_code == "1001":
                        # 返回前端 用户名密码不匹配
                        message = u"stat:fail:用户名密码不匹配:step2:{}:{}".format(result_code, task_id)
                    elif result_code == "1003":
                        # 返回前端 登录短信验证码输入错误
                        message = u"stat:fail:登录短信验证码不正确或过期:step2:{}:{}".format(result_code, task_id)
                    else:
                        # 返回前端 其它错误
                        message = u"stat:fail:其它错误:step2:{}:{}".format(result_code, task_id)

                    if is_success == False:
                        response['error_no'] = 1
                        response['task_no'] = task_no
                        response['message'] = message
                        response['timeout'] = 10
                        str_response = json.dumps(response)
                        self.request.send(str_response)
                    elif is_success == True:
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
                    # ret, message = mobile.login_sec_sms(sms_passwd)
                    ms_spider_3 = MobileShopSpider(task_id=task_id, phone=task_no, password=passwd, proc_num=task_no, step="SMS_crawl")
                    flag, result_code = ms_spider_3.check_sms_verifycode(sms_passwd)

                    if result_code == "1010":
                        # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
                        message = u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id)
                    elif result_code == "1004":
                        # 返回前端 爬取短信验证码校验失败
                        message = u"stat:fail:爬取短信验证码不正确或过期:step3:{}:{}".format(result_code, task_id)
                    else:
                        message = u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id)

                    if result_code == "0004":
                        flag, result_code = ms_spider_3.start_spider_details()
                        if result_code == "5000":
                            # 爬取短信验证码校验成功 下载入库成功
                            message = u"stat:total_success:爬取短信验证码校验成功且下载入库成功:step3:{}:{}".format(result_code, task_id)
                        elif result_code == "1010":
                            # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
                            message = u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id)
                        elif result_code == "4001":
                            # 返回前端 短信验证码校验成功但下载入库失败
                            message = u"stat:fail:短信验证码校验成功但下载入库失败:step3:{}:{}".format(result_code, task_id)
                        elif result_code == "3001":
                            # 返回前端 掉出登录
                            message = u"stat:fail:掉出登录:step3:{}:{}".format(result_code, task_id)
                        else:
                            message = u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id)

                    if flag == False:
                        response['error_no'] = 0
                        response['task_no'] = task_no
                        response['message'] = message
                        response['timeout'] = 10
                        str_response = json.dumps(response)
                        self.request.send(str_response)
                    elif flag == True:
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
        if data['method'] == 'login' and img_sms != None and img_sms != '':
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
            # self.mobile = UnicomSpider(task_no, passwd)
            # ret, message = self.mobile.login()
            self.mobile = unicom.Unicom(task_no, passwd)

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
                # self.mobile.spider_detail()
                self.mobile.spider()

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
            self.logger.info(u'n字符串不是json格式')
            self.logger.info(traceback.format_exc())

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
            self.logger.info(u'json对象转json字符串异常')
            self.logger.info(traceback.format_exc())
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
            time.sleep(1)

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
    host = 'localhost'
    port = int(conf.get('server', 'port'))
    addr = (host, port)

    print 'server is running....'
    server = SocketServer.ThreadingTCPServer(addr, Servers)
    server.serve_forever()

if __name__ == '__main__':
    main()
