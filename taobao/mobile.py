# -*- coding:utf-8 -*-
"""
File Name : 'mobile'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/5' '9:23'
"""



import sys
import os
import time
from bs4 import BeautifulSoup as bs
import requests

from selenium import webdriver
from selenium.webdriver.common.action_chains import  ActionChains
import selenium.webdriver.support.ui as ui
import requests
import comm_log
import urlparse
import re
import ConfigParser
import MySQLdb

reload(sys)
sys.setdefaultencoding("utf-8")



class TransferAccounts(object):
    def __init__(self, username = '18662726006', passwd = '526280'):
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'
        }

        #数据库连接
        sql_pool = self.sql_connect()

        #不同类型
        self.keyword_call_type = {
            1: u"主叫",
            2: u"被叫",
        }

        self.keyword_trade_type = {
            1: u"本地",
            2: u"国内漫游",
            3: u"其他",
        }

        self.keyword_trade_away = {
            1: u"发送",
            2: u"接收",
            3: u"未知",
        }

        #selenium 登录
        self.homepage = 'http://www.10010.com'
        login_url = 'http://www.10010.com/'
        self.login_unicom(login_url, username, passwd)


def main():
    transfer_accounts = TransferAccounts()



if __name__ == '__main__':
    main()
    pass