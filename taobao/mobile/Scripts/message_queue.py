# -*- coding:utf-8 -*-

"""
File Name: message_queue.py
Version: 0.1
Description: 提供消息队列的使用接口

Author: gonghao
Date: 2016/7/20 13:42
"""

import os
import ConfigParser
import codecs
from mns.account import Account
from mns.queue import Message
from mns.queue import MNSExceptionBase


def config_parse(parse_name="Ali_MNS"):
    """
    根据给定的消息队列的名称，解析配置
    :param parse_name: 配置文件的Sec_name
    :return:
    """
    cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
    cfg_path = os.path.join(cur_script_dir, "db.conf")

    cfg_reader = ConfigParser.ConfigParser()
    sec_name = parse_name
    cfg_reader.readfp(codecs.open(cfg_path, "r", "utf_8"))

    access_key_id = str(cfg_reader.get(sec_name, "AccessKeyId"))
    access_key_secret = str(cfg_reader.get(sec_name, "AccessKeySecret"))
    end_point = str(cfg_reader.get(sec_name, "Endpoint"))
    security_token = ""

    return access_key_id, access_key_secret, end_point, security_token


def send_msg(queue_name, message_body):
    """
    向指定消息队列发送消息
    :param queue_name: 消息队列的名称
    :param message_body: 需要发送的消息
    :return: True：发送成功；False：发送失败；None：该消息队列不存在
    """
    access_key_id, access_key_secret, end_point, security_token = config_parse()
    my_account = Account(end_point, access_key_id, access_key_secret, security_token)
    my_queue = my_account.get_queue(queue_name)

    try:
        msg = Message(str(message_body))
        re_msg = my_queue.send_message(msg)
        # print re_msg.message_id
    except MNSExceptionBase as e:
        if e.type == "QueueNotExist":
            return None
        else:
            return False
    else:
        return True


def rece_del_msg(queue_name, wait_seconds=3):
    """
    从指定的消息队列中获取消息，默认等待3s，每次获取1个
    :param queue_name: 消息队列的名称
    :param wait_seconds: 等待时长
    :return: (None, ""): 队列不存在；(False, ""): 获取失败；(True, "***"): 获取成功
    """
    access_key_id, access_key_secret, end_point, security_token = config_parse()
    my_account = Account(end_point, access_key_id, access_key_secret, security_token)
    my_queue = my_account.get_queue(queue_name)

    try:
        receive_message = my_queue.receive_message(wait_seconds)
    except MNSExceptionBase as e:
        if e.type == "QueueNotExist":
            result = (None, "")
        elif e.type == "MessageNotExist":
            result = (True, "")
        else:
            result = (False, "")
    else:
        result = (True, receive_message.message_body)

        try:
            my_queue.delete_message(receive_message.receipt_handle)
        except Exception as e:
            result = (False, "")

    return result


def get_queue_name(queue_keyword):
    """
    根据queue_keyword，获取对应的队列名称
    :param queue_keyword: 队列名称的关键词
    :return: [str]: 队列名
    """
    cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
    cfg_path = os.path.join(cur_script_dir, "db.conf")

    cfg_reader = ConfigParser.ConfigParser()
    sec_name = "QUEUE"
    cfg_reader.readfp(codecs.open(cfg_path, "r", "utf_8"))

    queue_name = str(cfg_reader.get(sec_name, queue_keyword))

    return queue_name

if __name__ == '__main__':
    import json

    # print send_msg(queue_name="QUEUE-CSD-SPIDER-BILL-RESULT-DEV",
    #                message_body=json.dumps({"Test": "It is a test."}))
    #
    # print "=" * 30
    #
    # flag, msg = rece_del_msg("QUEUE-CSD-SPIDER-BILL-RESULT-DEV")
    # while flag and msg != "":
    #     print flag
    #     print json.loads(msg)
    #     flag, msg = rece_del_msg("QUEUE-CSD-SPIDER-BILL-RESULT-DEV")

    flag, msg = rece_del_msg("QUEUE-CSD-SPIDER-VERIFY-BILL-DEV")
    while flag and msg != "":
        print json.loads(msg)
        flag, msg = rece_del_msg("QUEUE-CSD-SPIDER-VERIFY-BILL-DEV")

    # result = {
    #     "task_id": "t0002",
    #     "mobile": "18351826422",
    #     "if_success": True
    # }
    # result1 = {
    #     "task_id": "t0003",
    #     "mobile": "18351826422",
    #     "if_success": False
    # }
    # send_msg("QUEUE-CSD-SPIDER-BILL-RESULT-DEV", json.dumps(result))
    # send_msg("QUEUE-CSD-SPIDER-BILL-RESULT-DEV", json.dumps(result1))
