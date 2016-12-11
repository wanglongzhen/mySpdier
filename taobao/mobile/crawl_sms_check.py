#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'crawl_sms_check'.py 
Description: 接受爬取验证码并校验，如果成功，下载数据
Author: 'zhengyang' 
Date: '2016/11/3' '17:05'
"""

import time
import json
import sys
from Scripts.mobile_shop_spider import MobileShopSpider
from Scripts.redis_connect import redis_expire_status, redis_hset_status
from Scripts.message_queue import get_queue_name, rece_del_msg, send_msg
from Scripts.comm_log import comm_log
from Scripts.utils import get_phase_status
from Scripts.generate_report import generate_report

reload(sys)
sys.setdefaultencoding("utf-8")


def crawl_sms_check(proc_num, task_id, phone, sms_code, logger):
    """
    调用校验爬取短信验证码模块，如果校验成功，尝试爬取信息
    :param proc_num: 进程编号
    :param task_id: 任务ID
    :param phone: 手机号
    :param sms_code: 短信验证码
    :return:
    """
    logger.info(u"test:实例化MobileShopSpider")
    ms_spider = MobileShopSpider(task_id=task_id, phone=phone, password=None, proc_num=proc_num, step="SMS_crawl")

    logger.info(u"test:调用check_sms_verifycode")
    with ms_spider:
        flag, result_code = ms_spider.check_sms_verifycode(sms_code)

        # print result_code

        if result_code == "0004":
            # 爬取短信验证码校验成功 开始爬取
            values = get_phase_status(phase="SPIDER_SMS_SUCC")
        elif result_code == "1010":
            # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
            values = get_phase_status(phase="Service_NOT_NORMAL")
            logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))
        elif result_code == "1004":
            # 返回前端 爬取短信验证码校验失败
            values = get_phase_status(phase="SPIDER_SMS_FAIL_1")
            logger.error(u"stat:fail:爬取短信验证码不正确或过期:step3:{}:{}".format(result_code, task_id))
        else:
            values = get_phase_status(phase="Service_NOT_NORMAL")
            logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))

        redis_hset_status(task_id=task_id, values=json.dumps(values))
        if values["progress"] == 100:
            # 设置该任务状态存储在Redis中的超时时间（1天后自动删除）
            redis_expire_status(task_id=task_id)

        if result_code == "0004":
            flag, result_code = ms_spider.start_spider_details()

            # print result_code

            if result_code == "5000":
                # 爬取短信验证码校验成功 下载入库成功
                values = get_phase_status(phase="STORE")
                logger.info(u"stat:total_success:爬取短信验证码校验成功且下载入库成功:step3:{}:{}".
                            format(result_code, task_id))
            elif result_code == "1010":
                # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
                values = get_phase_status(phase="Service_NOT_NORMAL")
                logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))
            elif result_code == "4001":
                # 返回前端 短信验证码校验成功但下载入库失败
                values = get_phase_status(phase="FILE_OPERATION_FAILED")
                logger.error(u"stat:fail:短信验证码校验成功但下载入库失败:step3:{}:{}".format(result_code, task_id))
            elif result_code == "3001":
                # 返回前端 掉出登录
                values = get_phase_status(phase="LOGIN_FAILED_BY_COOKIE")
                logger.error(u"stat:fail:掉出登录:step3:{}:{}".format(result_code, task_id))
            else:
                values = get_phase_status(phase="Service_NOT_NORMAL")
                logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))

            # 更新任务状态
            redis_hset_status(task_id=task_id, values=json.dumps(values))
            if values["progress"] == 100:
                # 设置该任务状态存储在Redis中的超时时间（1天后自动删除）
                redis_expire_status(task_id=task_id)

    if not flag:
        logger.info(u"{}:{}任务失败 推送失败信息".format(task_id, phone))
        queue_name = get_queue_name("BillResult")
        msg = {
            "task_id": task_id,
            "mobile": phone,
            "bills": [],
            "result": False
        }
        send_msg(queue_name, json.dumps(msg))

    else:
        logger.info(u"{}:{}任务成功 生成报告".format(task_id, phone))
        # 生成报告
        generate_report(proc_num, task_id, phone)

        # 更新任务状态
        values = get_phase_status(phase="DONE")
        redis_hset_status(task_id=task_id, values=json.dumps(values))
        # 设置该任务状态存储在Redis中的超时时间（1天后自动删除）
        redis_expire_status(task_id=task_id)

        # 发送到消息队列（供推送使用）
        queue_name = get_queue_name("BillResult")
        msg = {
            "task_id": task_id,
            "mobile": phone,
            "bills": [],
            "result": True
        }
        send_msg(queue_name, json.dumps(msg))


def crawl_sms_check_flow(proc_num):
    """
    获取消息队列中的任务，并传入登录函数验证是否能够成功登录
    :param proc_num: 进程编号
    :return:
    """

    while 1:
        logger = comm_log(proc_num)
        queue_name = get_queue_name("VerifyBill")

        # 1. 获取消息队列中的任务
        # 消息队列样式 "task_id": "test1","mobile": "18794224550","sms_code": "112233"}
        flag, msg = rece_del_msg(queue_name)
        # print flag, msg
        if flag is None:
            logger.critical(u"无法连接到爬取短信验证码的消息队列")

        if flag and msg != "":
            msg_json = json.loads(msg)
            task_id = str(msg_json.get("task_id"))
            phone = str(msg_json.get("mobile"))
            sms_code = str(msg_json.get("sms_code"))

            logger.info(u"获取到新的任务:爬取短信验证码:{}:{}".format(task_id, phone))

            # 2. 校验爬取验证码
            try:
                crawl_sms_check(proc_num, task_id, phone, sms_code, logger)
            except Exception as e:
                logger.critical(u"校验爬取短信验证码:{}".format(str(e)))
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
    crawl_sms_check_flow(301)
