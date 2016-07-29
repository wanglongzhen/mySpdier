# -*- coding:utf-8 -*-
"""
File Name : 'login'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/7/29' '13:31'
"""



import os
import time
import traceback
from bs4 import BeautifulSoup as bs
import requests
import cookielib


class DoubanSpider(object):
    def __init__(self, username = '56669071@qq.com', passwd = '1qaz@WSX'):
        self.username = username
        self.passwd = passwd

        self.login()
        ret= self.r.get('https://www.douban.com/group/topic/83526522/')

        soup = bs(ret.text, 'html.parser')
        print ret.cookies
        pass

    def login(self):
        index_page_url = 'https://www.douban.com/'

        req = requests.session()
        headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
        }

        ret = req.get(index_page_url, headers = headers, cookies = req.cookies)
        print ret.cookies
        soup = bs(ret.text, 'html.parser')

        img_url = soup.find('div', class_ = 'item item-captcha').find('img', class_ = 'captcha_image').get('src')
        with open('1.png', 'wb') as t:
            img = req.get(img_url)
            t.write(img.content)
            img_id = raw_input("please input image code:")

        captcha_id = soup.find('input', attrs = {'name' : 'captcha-id'}).get('value')

        #log in
        login_url = 'https://www.douban.com/accounts/login'
        log_param = {
            'source' : 'index_nav',
            'form_email' : self.username,
            'form_password' : self.passwd,
            "remember": "on",
            'captcha-solution': img_id,
            'captcha-id' : captcha_id
        }

        ret = req.post(login_url, log_param, headers = headers)

        for cookie in ret.cookies:
            print cookie
            if cookie.name == 'ck':
                self.ck = cookie.value

        req.cookies = ret.cookies
        self.r = req

        pass

def main():
    spider = DoubanSpider()

    pass

if __name__ == '__main__':
    main()

