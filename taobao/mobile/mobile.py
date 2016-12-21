#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'simple_crawl'.py
Description: 本地测试I 测试MobileShopSpiderb本身
Author: 'zhengyang'
Date: '2016/11/2' '17:36'
"""


import time
import comm_log

from Scripts.mobile_shop_spider import MobileShopSpider

task_id = "cmcc_web_{:13.0f}".format(time.time() * 1000)


# 20161107已测试: 江苏 湖北 陕西 甘肃 山西 河北 四川 山东(停机) 福建
# todo 山西账单周期是入网时间开始的，不是固定每月一号

# 20161108已测试：江西 安徽（短信地点可能是梦网短信网内短信这种） 广西 黑龙江（格式略有不同见单元测试）河南 云南

# 20161109测试: 广州（对方号码可能是-） 北京（卡太小不好用） 重庆


phone = "13605394093"
passwd = "861357"
proc_num = "101"


start_time = time.time()
# 登录
ms_spider_1 = MobileShopSpider(task_id=task_id, phone=phone, password=passwd, proc_num=proc_num, step="Login")
logger = comm_log.comm_log()

with ms_spider_1:
    is_success, code = ms_spider_1.login()
    if code == "0001":
        # 触发短信验证码成功 返回前端 登录需要短信验证码
        # values = get_phase_status(phase="LOGIN_NEED_SMS")
        logger.info(u"stat:success:触发登录短信验证码成功:step1:{}:{}".format(code, task_id))
    elif code == "1010":
        # result_code 为 1010 时
        # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
        # values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fali:移动服务异常:step1:{}:{}".format(code, task_id))
    else:
        # 返回前端 其它错误 (不会发生)
        # values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:其它错误:step1:{}:{}".format(code, task_id))
if is_success:
    sms = raw_input(u"请输入短信验证码:")
else:
    # ms_spider_1.get_status(is_success=False)
    exit(1)

# 校验老的短信验证码 触发新的短信验证码
ms_spider_2 = MobileShopSpider(task_id=task_id, phone=phone, password=passwd, proc_num=proc_num, step = "SMS_login")
with ms_spider_2:
    is_success, result_code = ms_spider_2.get_sms_verifycode(sms)
    if result_code == "0003":
        # 登录短信验证码成功 请求发送爬取短信验证码
        # values = get_phase_status(phase="SPIDER_NEED_SMS")
        logger.info(u"stat:success:登录短信验证码校验成功:step2:{}:{}".format(result_code, task_id))
    elif result_code == "1010":
        # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）or 请求爬取短信验证码失败
        # values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:移动服务异常:step2:{}:{}".format(result_code, task_id))
    elif result_code == "1001":
        # 返回前端 用户名密码不匹配
        # values = get_phase_status(phase="PASSWORD_NOT_MATCH")
        logger.error(u"stat:fail:用户名密码不匹配:step2:{}:{}".format(result_code, task_id))
    elif result_code == "1003":
        # 返回前端 登录短信验证码输入错误
        # values = get_phase_status(phase="LOGIN_SMS_FAIL_1")
        logger.error(u"stat:fail:登录短信验证码不正确或过期:step2:{}:{}".format(result_code, task_id))
    else:
        # 返回前端 其它错误
        # values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:其它错误:step2:{}:{}".format(result_code, task_id))
if is_success:
    sms = raw_input(u"请输入二次短信验证码:")
else:
    # ms_spider_2.get_status(is_success=False)
    exit(1)

ms_spider_3 = MobileShopSpider(task_id=task_id, phone=phone, password=passwd, proc_num=proc_num, step = "SMS_crawl")
with ms_spider_3:
    is_success = ms_spider_3.check_sms_verifycode(sms)
    if result_code == "0004":
        # 爬取短信验证码校验成功 开始爬取
        # values = get_phase_status(phase="SPIDER_SMS_SUCC")
        pass
        # logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))
    elif result_code == "1010":
        # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
        # values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))
    elif result_code == "1004":
        # 返回前端 爬取短信验证码校验失败
        # values = get_phase_status(phase="SPIDER_SMS_FAIL_1")
        logger.error(u"stat:fail:爬取短信验证码不正确或过期:step3:{}:{}".format(result_code, task_id))
    else:
        # values = get_phase_status(phase="Service_NOT_NORMAL")
        logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))

    # redis_hset_status(task_id=task_id, values=json.dumps(values))
    if result_code == "0004":
        flag, result_code = ms_spider_3.start_spider_details()

        # print result_code

        if result_code == "5000":
            # 爬取短信验证码校验成功 下载入库成功
            # values = get_phase_status(phase="STORE")
            logger.info(u"stat:total_success:爬取短信验证码校验成功且下载入库成功:step3:{}:{}".
                        format(result_code, task_id))
        elif result_code == "1010":
            # 返回前端 可能移动服务存在异常，请稍后再试（也有可能是移动的接口发生更改）
            # values = get_phase_status(phase="Service_NOT_NORMAL")
            logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))
        elif result_code == "4001":
            # 返回前端 短信验证码校验成功但下载入库失败
            # values = get_phase_status(phase="FILE_OPERATION_FAILED")
            logger.error(u"stat:fail:短信验证码校验成功但下载入库失败:step3:{}:{}".format(result_code, task_id))
        elif result_code == "3001":
            # 返回前端 掉出登录
            # values = get_phase_status(phase="LOGIN_FAILED_BY_COOKIE")
            logger.error(u"stat:fail:掉出登录:step3:{}:{}".format(result_code, task_id))
        else:
            # values = get_phase_status(phase="Service_NOT_NORMAL")
            logger.error(u"stat:fail:移动服务异常:step3:{}:{}".format(result_code, task_id))
    # ms_spider_3.start_spider_details()


if not is_success:
    # ms_spider.get_status(is_success=False)
    exit(1)

# generate_report(proc_num=0, task_id=task_id, phone=phone)

print u"总时间:", time.time() - start_time



