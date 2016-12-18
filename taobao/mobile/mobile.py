#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'simple_crawl'.py
Description: 本地测试I 测试MobileShopSpiderb本身
Author: 'zhengyang'
Date: '2016/11/2' '17:36'
"""


import time

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

with ms_spider_1:
    is_success, code = ms_spider_1.login()
    # print is_success, code
if is_success:
    sms = raw_input(u"请输入短信验证码:")
else:
    # ms_spider_1.get_status(is_success=False)
    exit(1)

# 校验老的短信验证码 触发新的短信验证码
ms_spider_2 = MobileShopSpider(task_id=task_id, phone=phone, password=passwd, proc_num=proc_num, step = "SMS_login")
with ms_spider_2:
    is_success = ms_spider_2.get_sms_verifycode(sms)

if is_success:
    sms = raw_input(u"请输入二次短信验证码:")
else:
    # ms_spider_2.get_status(is_success=False)
    exit(1)

ms_spider_3 = MobileShopSpider(task_id=task_id, phone=phone, password=passwd, proc_num=proc_num, step = "SMS_crawl")
with ms_spider_3:
    is_success = ms_spider_3.check_sms_verifycode(sms)
    ms_spider_3.start_spider_details()


if not is_success:
    # ms_spider.get_status(is_success=False)
    exit(1)

# generate_report(proc_num=0, task_id=task_id, phone=phone)

print u"总时间:", time.time() - start_time



