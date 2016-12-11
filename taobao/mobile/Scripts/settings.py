#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'settings'.py 
Description:
Author: 'zhengyang' 
Date: '2016/10/25' '11:42'
"""

import time
import random

# 爬取移动短信/通话详单时的服务异常信息 首见于江西移动
DETAIL_FAIL_INFO = u"not login.but must login.sso flag"

REDIS_META_TABLE = "cmcc_web_meta:"
REDIS_STATUS_TABLE = "cmcc_web_status:"

# 重试次数
RETRY_TIMES = 3

# 重试等待时间
DELAY_TIME = 0.5

# 基本的headers
user_agent_list = ["Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
                   "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
                   "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
                   "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
                   "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;",
                   "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
                   "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
                   "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
                   "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11"
                   ]

user_agent = random.choice(user_agent_list)

headers = {
    "pre_login": {"Host": "www.10086.cn",
              "Connection": "keep-alive",
              "User-Agent": user_agent,
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
              "Accept-Encoding": "gzip, deflate, sdch",
              "Accept-Language": "zh-CN,zh;q=0.8"},

    "login": {"Host": "login.10086.cn",
              "Connection": "keep-alive",
              "Upgrade-Insecure-Requests": "1",
              "User-Agent": user_agent,
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
              "Accept-Encoding": "gzip, deflate, sdch, br",
              "Accept-Language": "zh-CN,zh;q=0.8"},

    "login_captchazh": {"Host": "login.10086.cn",
                        "Connection": "keep-alive",
                        "User-Agent": user_agent,
                        "Accept": "image/webp,image/*,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, sdch, br",
                        "Accept-Language": "zh-CN,zh;q=0.8",
                        "Referer": "https://login.10086.cn/html/login/login.html?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1"},


    "login_send": {"Host": "login.10086.cn",
                   "Connection": "keep-alive",
                   "User-Agent": user_agent,
                   "Accept": "application/json, text/javascript, */*; q=0.01",
                   "Accept-Encoding": "gzip, deflate, br",
                   "Accept-Language": "zh-CN,zh;q=0.8",
                   "Referer": "https://login.10086.cn/html/login/login.html?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1",
                   "X-Requested-With": "XMLHttpRequest",
                   "Origin": "https://login.10086.cn"
                   },

    "login_need_verify": {"Host": "login.10086.cn",
                   "Connection": "keep-alive",
                   "User-Agent": user_agent,
                   "Accept": "application/json, text/javascript, */*; q=0.01",
                   "Accept-Encoding": "gzip, deflate, br",
                   "Accept-Language": "zh-CN,zh;q=0.8",
                   "Referer": "https://login.10086.cn/html/login/login.html?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1",
                   "X-Requested-With": "XMLHttpRequest",
                   },

    "login_png": {"Host": "login.10086.cn",
                          "Connection": "keep-alive",
                          "User-Agent": user_agent,
                          "Accept": "image/webp,image/*,*/*;q=0.8",
                          "Accept-Encoding": "gzip, deflate, br",
                          "Accept-Language": "zh-CN,zh;q=0.8",
                          "Referer": "https://login.10086.cn/html/login/login.html?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1"
                          },

    "login_post": {"Host": "login.10086.cn",
                   "Connection": "keep-alive",
                   "User-Agent": user_agent,
                   "Accept": "application/json, text/javascript, */*; q=0.01",
                   "Accept-Encoding": "gzip, deflate, sdch",
                   "Accept-Language": "zh-CN,zh;q=0.8",
                   "Referer": "https://login.10086.cn/html/login/login.html?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1",
                   "X-Requested-With": "XMLHttpRequest",
                   },

    "login_auth": {"Host": "shop.10086.cn",
                   "Connection": "keep-alive",
                   "User-Agent": user_agent,
                   "Upgrade-Insecure-Requests": "1",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                   "Accept-Encoding": "gzip, deflate, sdch",
                   "Accept-Language": "zh-CN,zh;q=0.8"
                   },


    "get_sms_check_0": {"Host": "shop.10086.cn",
                        "Connection": "keep-alive",
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, sdch, br",
                        "Accept-Language": "zh-CN,zh;q=0.8",
                        "Referer": "http://shop.10086.cn/mall_100_100.html"
                        },

    "get_sms_check_1": {"Host": "shop.10086.cn",
                        "Connection": "keep-alive",
                        "User-Agent": user_agent,
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "Accept-Encoding": "gzip, deflate, sdch",
                        "Accept-Language": "zh-CN,zh;q=0.8",
                        "Referer": "http://shop.10086.cn/i/?f=billdetailqry",
                        "X-Requested-With": "XMLHttpRequest",
                        },

    "get_sms_check_2": {"Host": "login.10086.cn",
                        "Connection": "keep-alive",
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, sdch",
                        "Accept-Language": "zh-CN,zh;q=0.8",
                        "Referer": "http://shop.10086.cn/i/?f=billdetailqry"
                        },

    "get_sms_check_3":  {"Host": "shop.10086.cn",
                        "Connection": "keep-alive",
                        "User-Agent": user_agent,
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate, sdch",
                        "Accept-Language": "zh-CN,zh;q=0.8",
                        "Referer": "http://shop.10086.cn/i/?f=billdetailqry",
                        "X-Requested-With": "XMLHttpRequest",
                        },


    "get_sms_verifycode_1": {"Host": "shop.10086.cn",
                             "Connection": "keep-alive",
                             "User-Agent": user_agent,
                             "Accept": "*/*",
                             "Accept-Encoding": "gzip, deflate, sdch, br",
                             "Accept-Language": "zh-CN,zh;q=0.8",
                             "Referer": "http://shop.10086.cn/i/?f=home",
                             "X-Requested-With": "XMLHttpRequest",
                             },



    "get_sms_verifycode_2": {"Host": "login.10086.cn",
                             "Connection": "keep-alive",
                             "User-Agent": user_agent,
                             "Accept": "*/*",
                             "Accept-Encoding": "gzip, deflate, sdch, br",
                             "Accept-Language": "zh-CN,zh;q=0.8",
                             "Referer": "http://shop.10086.cn/i/?f=home",
                             "X-Requested-With": "XMLHttpRequest",
                             },

    "check_sms_verifycode": {"Host": "login.10086.cn",
                             "Connection": "keep-alive",
                             "User-Agent": user_agent,
                             "Accept": "*/*",
                             "Accept-Encoding": "gzip, deflate, sdch, br",
                             "Accept-Language": "zh-CN,zh;q=0.8",
                             "Referer": "http://shop.10086.cn/i/?f=home",
                             },

    "_get_detail":  {"Host": "shop.10086.cn",
                             "Connection": "keep-alive",
                             "User-Agent": user_agent,
                             "Accept": "*/*",
                             "Accept-Encoding": "gzip, deflate, sdch, br",
                             "Accept-Language": "zh-CN,zh;q=0.8",
                             "Referer": "http://shop.10086.cn/i/?f=home",
                             },


    "_get_basic": {"Host": "shop.10086.cn",
                  "Connection": "keep-alive",
                  "User-Agent": user_agent,
                  "Accept": "application/json, text/javascript, */*; q=0.01",
                  "Accept-Encoding": "gzip, deflate, sdch, br",
                  "Accept-Language": "zh-CN,zh;q=0.8",
                  "Referer": "http://shop.10086.cn/i/?f=home",
                  "X-Requested-With": "XMLHttpRequest",
                  "Referer": "http://shop.10086.cn/i/?f=custinfoqry",
                  },









}


def get_wf_fpc():
    """模拟生成WF_FPC cookie值
    :return [str] WF_FPC cookie值"""
    i, co_f = "{:13.0f}".format(time.time() * 1000), "2"

    for h in range(2, 32 - len(i) + 1):
        t = int(random.random() * 16)
        co_f += format(t, 'x')

    co_f += i
    id_, lv, ss = co_f, "{:13.0f}".format(time.time() * 1000), "{:13.0f}".format(time.time() * 1000)
    wf_fpc = "id={id_}:lv={lv}:ss={ss}".format(id_=id_, lv=lv, ss=ss)
    return wf_fpc

# provinces_json是从移动登录页的js文件中获得的
provinces_json = [
    {"code": 100, "name": "北京", "href": "http://www.10086.cn/bj", "url": "http://shop.10086.cn/mall_100_100.html",
     "abbr": "bj"},
    {"code": 551, "name": "安徽", "href": "http://www.10086.cn/ah", "url": "http://shop.10086.cn/mall_551_551.html",
     "abbr": "ah"},
    {"code": 230, "name": "重庆", "href": "http://www.10086.cn/cq", "url": "http://shop.10086.cn/mall_230_230.html",
     "abbr": "cq"},
    {"code": 591, "name": "福建", "href": "http://www.10086.cn/fj", "url": "http://shop.10086.cn/mall_591_591.html",
     "abbr": "fj"},
    {"code": 200, "name": "广东", "href": "http://www.10086.cn/gd", "url": "http://shop.10086.cn/mall_200_200.html",
     "abbr": "gd"},
    {"code": 771, "name": "广西", "href": "http://www.10086.cn/gx", "url": "http://shop.10086.cn/mall_771_771.html",
     "abbr": "gx"},
    {"code": 931, "name": "甘肃", "href": "http://www.10086.cn/gs", "url": "http://shop.10086.cn/mall_931_931.html",
     "abbr": "gs"},
    {"code": 851, "name": "贵州", "href": "http://www.10086.cn/gz", "url": "http://shop.10086.cn/mall_851_851.html",
     "abbr": "gz"},
    {"code": 311, "name": "河北", "href": "http://www.10086.cn/he", "url": "http://shop.10086.cn/mall_311_311.html",
     "abbr": "he"},
    {"code": 371, "name": "河南", "href": "http://www.10086.cn/ha", "url": "http://shop.10086.cn/mall_371_371.html",
     "abbr": "ha"},
    {"code": 898, "name": "海南", "href": "http://www.10086.cn/hi", "url": "http://shop.10086.cn/mall_898_898.html",
     "abbr": "hi"},
    {"code": 270, "name": "湖北", "href": "http://www.10086.cn/hb", "url": "http://shop.10086.cn/mall_270_270.html",
     "abbr": "hb"},
    {"code": 731, "name": "湖南", "href": "http://www.10086.cn/hn", "url": "http://shop.10086.cn/mall_731_731.html",
     "abbr": "hn"},
    {"code": 451, "name": "黑龙江", "href": "http://www.10086.cn/hl", "url": "http://shop.10086.cn/mall_451_451.html",
     "abbr": "hl"},
    {"code": 431, "name": "吉林", "href": "http://www.10086.cn/jl", "url": "http://shop.10086.cn/mall_431_431.html",
     "abbr": "jl"},
    {"code": 250, "name": "江苏", "href": "http://www.10086.cn/js", "url": "http://shop.10086.cn/mall_250_250.html",
     "abbr": "js"},
    {"code": 791, "name": "江西", "href": "http://www.10086.cn/jx", "url": "http://shop.10086.cn/mall_791_791.html",
     "abbr": "jx"},
    {"code": 240, "name": "辽宁", "href": "http://www.10086.cn/ln", "url": "http://shop.10086.cn/mall_240_240.html",
     "abbr": "ln"},
    {"code": 471, "name": "内蒙古", "href": "http://www.10086.cn/nm", "url": "http://shop.10086.cn/mall_471_471.html",
     "abbr": "nm"},
    {"code": 951, "name": "宁夏", "href": "http://www.10086.cn/nx", "url": "http://shop.10086.cn/mall_951_951.html",
     "abbr": "nx"},
    {"code": 971, "name": "青海", "href": "http://www.10086.cn/qh", "url": "http://shop.10086.cn/mall_971_971.html",
     "abbr": "qh"},
    {"code": 210, "name": "上海", "href": "http://www.10086.cn/sh", "url": "http://shop.10086.cn/mall_210_210.html",
     "abbr": "sh"},
    {"code": 280, "name": "四川", "href": "http://www.10086.cn/sc", "url": "http://shop.10086.cn/mall_280_280.html",
     "abbr": "sc"},
    {"code": 531, "name": "山东", "href": "http://www.10086.cn/sd", "url": "http://shop.10086.cn/mall_531_531.html",
     "abbr": "sd"},
    {"code": 351, "name": "山西", "href": "http://www.10086.cn/sx", "url": "http://shop.10086.cn/mall_351_351.html",
     "abbr": "sx"},
    {"code": 290, "name": "陕西", "href": "http://www.10086.cn/sn", "url": "http://shop.10086.cn/mall_290_290.html",
     "abbr": "sn"},
    {"code": 220, "name": "天津", "href": "http://www.10086.cn/tj", "url": "http://shop.10086.cn/mall_220_220.html",
     "abbr": "tj"},
    {"code": 991, "name": "新疆", "href": "http://www.10086.cn/xj", "url": "http://shop.10086.cn/mall_991_991.html",
     "abbr": "xj"},
    {"code": 891, "name": "西藏", "href": "http://www.10086.cn/xz", "url": "http://shop.10086.cn/mall_891_891.html",
     "abbr": "xz"},
    {"code": 871, "name": "云南", "href": "http://www.10086.cn/yn", "url": "http://shop.10086.cn/mall_871_871.html",
     "abbr": "yn"},
    {"code": 571, "name": "浙江", "href": "http://www.10086.cn/zj", "url": "http://shop.10086.cn/mall_571_571.html",
     "abbr": "zj"}
]




