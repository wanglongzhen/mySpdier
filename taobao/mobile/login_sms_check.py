# -*- coding:utf-8 -*-

"""
File Name: login.py
Version: 0.1
Description: 接受登录验证码并校验，如果成功，触发爬取验证码

Author: zy
Date: 2016/6/24 9:49
"""
import time
import json
import sys
from Scripts.mobile_shop_spider import MobileShopSpider
from Scripts.redis_connect import redis_expire_status, redis_hset_status
from Scripts.message_queue import get_queue_name, rece_del_msg
from Scripts.comm_log import comm_log
from Scripts.utils import get_phase_status

reload(sys)
sys.setdefaultencoding("utf-8")


def login_sms_check(proc_num, task_id, phone, sms_code, logger):
    """
    调用校验登录短信验证码模块，验证是否能够成功登录，如果能成功登录，尝试触发爬取短信验证码
    :param proc_num: 进程编号
    :param task_id: 任务ID
    :param phone: 手机号
    :param sms_code: 短信验证码
    :param logger: 打印日志的对象
    :return:
    """
    logger.info(u"test:实例化MobileShopSpider")
    ms_spider = MobileShopSpider(task_id=task_id, phone=phone, password=None, proc_num=proc_num, step="SMS_login")

    logger.info(u"test:调用get_sms_verifycode")
    with ms_spider:
        _, result_code = ms_spider.get_sms_verifycode(sms_code)

    if result_code == "0003":
        # 登录短信验证码成功 请求发送爬取短信验证码
        values = get_phase_status(phase="SPIDER_NEED_SMS")
        logger.info(u"stat:success:登录短信验证码校验成功:step2:{}:{}".format(result_code, task_id))
    elif result_code == "1010":
        # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）or 请求爬取短信验证码失败
        values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:移动服务异常:step2:{}:{}".format(result_code, task_id))
    elif result_code == "1001":
        # 返回前端 用户名密码不匹配
        values = get_phase_status(phase="PASSWORD_NOT_MATCH")
        logger.error(u"stat:fail:用户名密码不匹配:step2:{}:{}".format(result_code, task_id))
    elif result_code == "1003":
        # 返回前端 登录短信验证码输入错误
        values = get_phase_status(phase="LOGIN_SMS_FAIL_1")
        logger.error(u"stat:fail:登录短信验证码不正确或过期:step2:{}:{}".format(result_code, task_id))
    else:
        # 返回前端 其它错误
        values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:其它错误:step2:{}:{}".format(result_code, task_id))

    # 更新任务状态
    redis_hset_status(task_id=task_id, values=json.dumps(values))
    if values["progress"] == 100:
        # 设置该任务状态存储在Redis中的超时时间（1天后自动删除）
        redis_expire_status(task_id=task_id)


def login_sms_check_flow(proc_num):
    """
    获取消息队列中的任务，并传入登录函数验证是否能够成功登录
    :param proc_num: 进程编号
    :return:
    """

    while 1:
        logger = comm_log(proc_num)
        queue_name = get_queue_name("LoginSMS")

        # 1. 获取消息队列中的任务
        # 消息队列样式 task_list:
        # msg = {"task_id": "test1","mobile": "18794224550","sms_code": "123321"}
        flag, msg = rece_del_msg(queue_name)

        if flag is None:
            logger.critical(u"无法连接到登录任务的消息队列")

        if flag and msg != "":
            msg_json = json.loads(msg)
            task_id = str(msg_json.get("task_id"))
            phone = str(msg_json.get("mobile"))
            sms_code = str(msg_json.get("sms_code"))

            logger.info(u"获取到新的任务:登录短信验证码:{}:{}".format(task_id, phone))

            # 2. 校验登录短息验证码
            try:
                login_sms_check(proc_num, task_id, phone, sms_code, logger)
            except Exception as e:
                logger.critical(str(e))
                try:
                    values = get_phase_status(phase="Service_NOT_NORMAL")
                    redis_hset_status(task_id=task_id, values=json.dumps(values))
                    redis_expire_status(task_id=task_id)
                except Exception as e:
                    logger.critical(u"Reids服务出现异常:{}".format(str(e)))
        else:
            time.sleep(10)
            # break  # 测试使用，当没有消息时就退出

if __name__ == '__main__':
    login_sms_check_flow(201)