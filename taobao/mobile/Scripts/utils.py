#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'utils'.py
Description: 实用小工具和mongodb存储管道
Author: 'zhengyang' 
Date: '2016/9/29' '15:40'
"""

import re
import datetime
from dateutil.relativedelta import relativedelta
from settings import provinces_json


##################################################################
#                       数据处理函数                              #
##################################################################
def get_unit(unit_value):
    """套餐余量的单位
    04 --> MB
    01 --> 分钟"""
    if unit_value == "04":
        return "MB"
    elif unit_value == "03":
        return "MB"
    elif unit_value == "01":
        return u"分"
    else:
        return ""


def get_date(date_value):
    """将格式如2016年9月01日这样的日期转成yyyy-mm-dd格式
        例如:2016年9月01日 --> 2016-09-01
            2016年10月01日 --> 2016-10-01"""

    if not date_value:
        return ""

    try:
        year = re.findall(u'(\d+)年', date_value)[0]
    except IndexError:
        year = ""
    else:
        if len(year) == 2:
            year = "20" + year

    try:
        month = re.findall(u'(\d+)月', date_value)[0]
    except IndexError:
        month = ""
    else:
        if month in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            month = "0" + month

    try:
        day = re.findall(u'(\d+)日', date_value)[0]
    except IndexError:
        day = ""
    else:
        if day in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            day = "0" + day

    if year and month and day:
        new_date = year + "-" + month + "-" + day
    elif year and month:
        new_date = year + "-" + month
    elif year:
        new_date = year
    else:
        new_date = ""
    return new_date


def get_state(state):
    """将基本信息中的用户状态的文字描述转成数值"""
    if not state:
        return -1

    if state.find(u"正常") >= 0 or state.find(u"正使用") >= 0 or state.find(u"在网") >= 0 or state.find("00") >= 0:
        return 0
    elif state.find(u"单向停机") >= 0:
        return 1
    elif state.find(u"停机") >= 0:
        return 2
    elif state.find(u"预销户") >= 0:
        return 3
    elif state.find(u"销户") >= 0:
        return 4
    elif state.find(u"过户") >= 0:
        return 5
    elif state.find(u"改号") >= 0:
        return 6
    elif state.find(u"号码不存在") >= 0:
        return 99
    else:
        return -1


def get_value(value):
    """将金额字符串(单位是元)转成数值 单位为分
    例如:￥17.26 --> 1726
        19.89元 --> 1989
        -88元 --> -8800
        0.1 --> 10"""
    if not value:
        return 0

    # 整数或浮点数(如12.345)的正则表达式(可以带+-号)
    pattern = re.compile(r"[+-]?\d*\.\d+|\d+", re.S)
    try:
        value = re.findall(pattern, value)[0]
    except IndexError:
        # raise ValueError(u"输入格式不正确")
        return 0
    else:
        value_number = int(round(float(value) * 100))
        return value_number


def get_detail_time(start_time, month):
    """处理详单的发生时间 如果开始时间是20(年份)开头，保持不变，否则加上年份
     2016/08/26 09:09:50转换为2016-08-26 09:09:50"""
    if start_time.startswith("20"):
        detail_time = start_time
    else:
        detail_time = month[:4] + "-" + start_time

    detail_time = detail_time.replace("/", "-")

    return detail_time


def get_duration(duration):
    """将通信时长字符串转成数值 单位秒
        例如:1秒 --> 1
            2分3秒 --> 123
            1小时1分1秒 --> 3661
            1时1分1秒 --> 3661"""

    if not duration:
        return 0

    if duration.find(u"秒") > -1 or duration.find(u"分") > -1 or duration.find(u"时") > -1:
        # 含有时分秒的
        try:
            hours = re.findall(u'(\d+)(?:时|小时)', duration)[0]
        except IndexError:
            hours = 0
        else:
            hours = int(hours)

        try:
            minutes = re.findall(u'(\d+)分', duration)[0]
        except IndexError:
            minutes = 0
        else:
            minutes = int(minutes)

        try:
            seconds = re.findall(u'(\d+)秒', duration)[0]
        except IndexError:
            seconds = 0
        else:
            seconds = int(seconds)

    elif duration.find(":") > -1:
        # 01:23:45这种的
        duration_list = duration.split(":")

        try:
            hours = duration_list[-3]
        except IndexError:
            hours = 0
        else:
            hours = int(hours)

        try:
            minutes = duration_list[-2]
        except IndexError:
            minutes = 0
        else:
            minutes = int(minutes)

        try:
            seconds = duration_list[-1]
        except IndexError:
            seconds = 0
        else:
            seconds = int(seconds)

    else:
        return 0

    duration_number = hours * 60 * 60 + minutes * 60 + seconds
    return duration_number


def get_open_time(duration, current_day=datetime.datetime.now().date()):
    """将网龄转变成入网时间
    duration: 网龄
    格式如： 1年2个月3天(但类似一年两个月三天不适用)
            2个月1天
            3个月
    open_time: 入网时间 当前日期减去网龄 字符串类型 """

    if not duration:
        return ""

    try:
        years = re.findall(u'(\d+)年', duration)[0]
    except IndexError:
        years = 0
    else:
        years = int(years)

    try:
        months = re.findall(u'(\d+)(?: 月|个月)', duration)[0]
    except IndexError:
        months = 0
    else:
        months = int(months)

    try:
        days = re.findall(u'(\d+)天', duration)[0]
    except IndexError:
        days = 0
    else:
        days = int(days)

    # 年和月各按365天和30天计 获得以天为单位的网龄
    duration_day = years * 365 + months * 30 + days

    # 当天减去网龄 得到入网时间
    open_time = current_day - relativedelta(days=duration_day)
    open_time = open_time.strftime('%Y-%m-%d')
    return open_time


def get_dial_type(dial_type):
    """获得call的主被叫"""
    if not dial_type:
        return ""

    if dial_type.find(u"被叫") >= 0:
        return "DIALED"
    elif dial_type.find(u"主叫") >= 0:
        return "DIAL"
    else:
        return "DIALED"


def get_send_type(send_type):
    """获得sms的收发状态"""
    if not send_type:
        return ""
    if send_type.find(u"被叫") >= 0 or send_type.find(u"收取") >= 0 or send_type.find(u"接收") >= 0:
        return "RECEIVE"
    elif send_type.find(u"主叫") >= 0 or send_type.find(u"发送") >= 0:
        return "SEND"
    else:
        return "RECEIVE"


def get_msg_type(msg_type):
    """获得信息类型 msg_type"""
    if not msg_type:
        return ""
    if msg_type.find(u"短信") >= 0 or msg_type.find(u"短彩信") >= 0:
        return "SMS"
    elif msg_type.find(u"彩信") >= 0:
        return "MMS"
    else:
        return "SMS"


def get_jquery_detail(resp):
    """获得jQuery18305637221474059924_1477639014937($wanted_data)中的数据$wanted_data
    :param resp 字符串
    :return 字符串中需要的信息
    :raise ValueError 当resp格式改变，提取失败"""

    pattern = re.compile(r"jQuery\d+?_\d+?\((.*)\)", re.S)
    try:
        content = re.findall(pattern, resp)[0]
    except (IndexError, KeyError, TypeError) as e:
        raise ValueError(u"详单返回值格式改变:{}:{}".format(resp, e.args[0]))
    else:
        return content


##################################################################
#                   写入redis的爬取状态                            #
##################################################################
def get_phase_status(phase):
    """
    根据提供的 phase，返回对应的 values 信息（保存到Redis中的任务状态信息）
    :param phase: [str] 关键词
    :return: [dict] 任务状态信息
    """
    values = dict()
    values["description"] = u"正在登录"
    values["finished"] = False
    values["input"] = {"type": "", "value": "", "wait_seconds": ""}
    values["phase"] = "LOGIN"
    values["phase_value"] = "DOING"
    values["progress"] = 0
    values["code"] = "0000"

    if phase == "LOGIN":
        pass
    elif phase == "RECEIVE":
        values["description"] = u"正在爬取"
        values["phase"] = "RECEIVE"
        values["progress"] = 25
        values["code"] = "2000"
    elif phase == "PASSWORD_NOT_MATCH":
        values["description"] = u"用户名密码不匹配"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 100
        values["code"] = "1001"
    elif phase == "PASSWORD_TOO_SIMPLE":
        values["description"] = u"密码过于简单，请重置密码"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 100
        values["code"] = "1002"
    elif phase == "LOGIN_NEED_SMS":
        values["description"] = u"登录需要短信验证码"
        values["finished"] = False
        values["phase"] = "LOGIN"
        values["phase_value"] = "DOING"
        values["progress"] = 0
        values["code"] = "0001"
    elif phase == "LOGIN_SMS_FAIL_1":
        values["description"] = u"登录短信验证码输入错误"
        values["finished"] = False
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 0
        values["code"] = "1003"
    elif phase == "LOGIN_SMS_SUCC":
        values["description"] = u"登录短信验证码输入正确"
        values["finished"] = False
        values["phase"] = "LOGIN"
        values["phase_value"] = "DOING"
        values["progress"] = 0
        values["code"] = "0002"
    elif phase == "LOGIN_SMS_FAIL_2":
        values["description"] = u"登录短信验证码输入错误次数过多，登录失败"
        values["finished"] = True
        values["phase"] = "LOGIN"
        values["phase_value"] = "DONE"
        values["progress"] = 100
        values["code"] = "1005"
    elif phase == "SPIDER_NEED_SMS":
        values["description"] = u"爬取需要短信验证码"
        values["finished"] = False
        values["phase"] = "LOGIN"
        values["phase_value"] = "DOING"
        values["progress"] = 0
        values["code"] = "0003"
    elif phase == "SPIDER_SMS_FAIL_1":
        values["description"] = u"爬取所需短信验证码输入错误"
        values["finished"] = False
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 0
        values["code"] = "1004"
    elif phase == "SPIDER_SMS_SUCC":
        values["description"] = u"爬取所需短信验证码输入正确, 准备爬取"
        values["finished"] = False
        values["phase"] = "LOGIN"
        values["phase_value"] = "DOING"
        values["progress"] = 0
        values["code"] = "0004"
    elif phase == "SPIDER_SMS_FAIL_2":
        values["description"] = u"爬取短信验证码输错次数过多，登录爬取失败"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 100
        values["code"] = "1006"
    elif phase == "Service_NOT_NORMAL":
        values["description"] = u"移动服务存在异常，请稍后再试"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 100
        values["code"] = "1010"
    elif phase == "LOGIN_FAILED_BY_COOKIE":
        values["description"] = u"时间间隔太久，用户掉出登录，需要重新登录"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_TIMEOUT"
        values["progress"] = 100
        values["code"] = "3001"
    elif phase == "EXTRACT":
        values["description"] = u"正在解析"
        values["finished"] = False
        values["phase"] = "EXTRACT"
        values["phase_value"] = "DOING"
        values["progress"] = 50
        values["code"] = "4000"
    elif phase == "SOME_WRONG":  # 可能会存在一些文件没有下载成功，添加5次重试之后，应该不会出现这种情况
        values["description"] = u"正在解析"
        values["finished"] = False
        values["phase"] = "EXTRACT"
        values["phase_value"] = "DOING"
        values["progress"] = 50
        values["code"] = "4000"
    elif phase == "FILE_OPERATION_FAILED":
        values["description"] = u"文件操作失败"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_FAIL"
        values["progress"] = 100
        values["code"] = "4001"
    elif phase == "STORE":
        values["description"] = u"正在保存解析好的数据"
        values["finished"] = False
        values["phase"] = "STORE"
        values["phase_value"] = "DOING"
        values["progress"] = 75
        values["code"] = "5000"
    elif phase == "DONE":
        values["description"] = u"任务完成"
        values["finished"] = True
        values["phase"] = "DONE"
        values["phase_value"] = "DONE_SUCC"
        values["progress"] = 100
        values["code"] = "6000"
    else:
        values = {}

    return values


##################################################################
#                   移动商城的省份-代码字典                         #
##################################################################
def get_province_code(code, provinces_json=provinces_json):
    """根据省份代码得到对应的省份
    :param province_code_dict 省份代码
    :param provinces_json 从移动商城得到的省份代码-省份字典
    :return [str] 省份"""

    if isinstance(code, int):
        pass
    elif isinstance(code, str):
        try:
            code = int(code)
        except ValueError:
            raise ValueError(u"省份代码格式不正确")
    else:
        raise ValueError(u"省份代码格式不正确")

    province_code_dict = dict()
    for province in provinces_json:
        province_code_dict[province["code"]] = province["name"]

    return province_code_dict.get(code)




def get_query_datelist_0(breaktime=None):
    """
    breaktime 断点爬取的时候，breaktime为上次爬取的日期的后一天，breaktime(没有爬取）
    通过当前时间往前推6个月，返回一个[[begintime,endtime,strmonth],[begintime,endtime,strmonth]]
    :return:
    """

    def get_querytime_string(query_begintime, query_endtime):
        str_begintime = str(query_begintime)
        str_endtime = str(query_endtime)
        str_month = "{year}{month:02d}".format(year=query_begintime.year, month=query_begintime.month)
        return str_begintime, str_endtime, str_month

    query_list = []
    now = datetime.datetime.now()
    if now.day == 1:
        query_begintime = now + relativedelta(months=-1)
    else:
        # 当天为2号的时候，开始时间与结束时间是同一天
        query_begintime = datetime.date(now.year, now.month, 1)
    query_endtime = now.date() + relativedelta(days=-1)

    str_begintime, str_endtime, str_month = get_querytime_string(query_begintime, query_endtime)
    # 与断点比较，
    if breaktime is not None and breaktime >= str_begintime:
        #  如果断点与查询本月的结束时间相同，则返回[]
        if breaktime >= str_endtime:
            return []
        str_begintime = breaktime
        query_list.append([str_begintime, str_endtime, str_month])
        return query_list
    else:
        query_list.append([str_begintime, str_endtime, str_month])

    # 利用query_begintime 生成查询时间列表
    breakflg = False
    for _ in range(0, 6):
        tmptime = query_begintime
        query_begintime = tmptime + relativedelta(months=-1)
        query_endtime = tmptime + relativedelta(days=-1)
        str_begintime, str_endtime, str_month = get_querytime_string(query_begintime, query_endtime)

        # 断点时间，断点替换begintime，不再往断点前继续生成时间
        if breaktime is not None and str_begintime < breaktime < str_endtime:
            str_begintime = breaktime
            breakflg = True
        query_list.append([str_begintime, str_endtime, str_month])
        if breakflg:
            break

    return query_list

if __name__ == "__main__":
    # print get_province_code("abc")

    print get_detail_time("10/11 17:38:06", "201610")

