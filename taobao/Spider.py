# -*- coding:utf-8 -*-
"""
File Name : 'Spider'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/24' '21:00'
"""

from union import Union

class MobileSpider(Union):
    def __init__(self, username, passwd):
        Union.__init__(self, username)
        print 'MobileSpider init'


    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        Union.__exit__(self.exc_type, exc_val, exc_tb)

    def login(self):
        print 'MobileSpider login'
        pass

    def login_first_sms(self):
        print 'MobileSpider login_first_sms'
        pass

    def login_sec_sms(self):
        print 'MobileSpider login_sec_sms'
        pass

