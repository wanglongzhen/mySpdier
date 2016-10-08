# -*- coding:utf-8 -*-
"""
File Name : 'SocketServer'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/24' '20:32'
"""

from socket import *
import json
import base64

host = 'localhost'
port = 9999
bufsize = 10240
addr = (host, port)
client = socket(AF_INET, SOCK_STREAM)
client.connect(addr)

def unicom():
    while True:

        # 联通数据交互过程
        data = raw_input()
        # data = '{"method":"login","task_no":18513622865, "param": {"mobile_type":"unicom", "password":861357}}'
        # data = '{"method":"login","task_no":18662726006, "param": {"mobile_type":"unicom", "password":526280}}'

        if not data or data == 'exit':
            break
        print data
        client.send('%s\r\n' % data)
        data = client.recv(bufsize)
        if not data:
            break
        print data.strip()
        ret_json = json.loads(data)
        if ret_json['img_flag'] == 1:
            img_data = ret_json['img_data']
            # 处理图片数据
            img = base64.b64decode(img_data)
            dst_file = r'client_img.jpg'
            with open(dst_file, 'wb') as f:
                f.write(img)


            # 输入图片验证码
            data = raw_input()
            # data = '{"method":"login","task_no":18513622865, "param": {"mobile_type":"unicom", "password":861357, "img_sms":""}}'
            client.send('%s\r\n' % data)

        elif ret_json['img_flag'] == 0:
            print('登录成功')
            break
        elif ret_json['error_no'] == 1:
            print("登录失败")
    client.close()


def mobile():
    while True:

        # 移动数据交互过程
        #等待输入发送服务端的json串
        # data = '{"method":"login","task_no":18513622965, "param": {"mobile_type":"mobile", "password":978672}}'
        data = raw_input()


        if not data or data == 'exit':
            break
        print data
        client.send('%s\r\n' % data)
        data = client.recv(bufsize)

        print data.strip()
        ret_json = json.loads(data)
        if ret_json['error'] == '0':
            #触发登录短信验证码成功

            # 输入登录验证码
            data = raw_input()
            # data = '{"method":"login_sms","task_no":18513622865, "param": {"mobile_type":"unicom", "password":861357, "sms_passwd":123456}}'
            client.send('%s\r\n' % data)

            data = client.recv(bufsize)
            print data.strip()
            ret = json.loads(data)
            if ret['error_no'] == '0':
                #输入详单查询验证码
                data = raw_input()
                # data = '{"method":"login_vec","task_no":18513622965, "param": {"mobile_type":"unicom", "password":861357, "sms_passwd":123456}}'
                client.send('%s\r\n' % data)

                data = client.recv(bufsize)
                print data.strip()
                ret = json.loads(data)

                if ret['error_no'] == '0':
                    print("登录成功，下载详单成功")
                elif ret['error_no'] == '1' or ret['error_no'] == '2':
                    print ret['message']
                    break
            elif ret['error_no'] == '1' or ret['error_no'] == '2':
                print ret['message']
                break


        elif ret_json['error_no'] == '1' or ret_json['error_no']:
            print('登录失败')
            print ret_json['message']
            break
    client.close()


if __name__ == '__main__':

    #联通
    unicom()
    #移动
    # mobile()