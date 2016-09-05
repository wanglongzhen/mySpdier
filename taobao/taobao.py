# -*- coding:utf-8 -*-
"""
File Name : 'transferAccounts'.py
Description:
Author: 'wanglongzhen'
Date: '2016/8/1' '11:46'
"""


import os
import time
import traceback
from bs4 import BeautifulSoup as bs
import requests
import cookielib
import datetime
import image_to_string

import socket

from selenium import webdriver
from selenium.webdriver.common.action_chains import  ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import requests

from selenium.webdriver.common.keys import Keys

class TransferAccounts(object):
    def __init__(self, username = 'wanglongzhen_2008', passwd = 'wlz9087881'):

        print str(int(time.time() * 1000))
        # login_url = 'https://auth.alipay.com/login/index.htm'
        login_url = 'https://login.taobao.com/member/login.jhtml'
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'
        }

        #self.login(login_url, username, passwd)

        #selenium 登录
        login_url = 'https://login.tmall.com/'
        # self.sele_login(login_url, username, passwd)
        self.login_tmall(login_url, username, passwd)

    def login_tmall(self, login_url, user, passwd):
        #driver = webdriver.PhantomJS()
        driver = webdriver.Firefox()
        driver.maximize_window()
        driver.delete_all_cookies()

        driver.get(login_url)

        frame = driver.find_element_by_xpath('//iframe[@id="J_loginIframe"]')
        driver.switch_to.frame(frame)

        element=driver.find_element_by_id('J_Quick2Static')
        element.click()
        driver.implicitly_wait(20)
        username = driver.find_element_by_id('TPL_username_1')
        if not username.is_displayed():
            driver.implicitly_wait(20)
            driver.find_element_by_xpath("//*[@id='J_Quick2Static']").click()

        driver.implicitly_wait(20)
        username.send_keys(user)

        driver.find_element_by_id('TPL_password_1').send_keys(passwd)
        driver.implicitly_wait(20)

        lang = driver.find_element_by_id('nc_1_n1z')
        if lang.is_displayed():
            ActionChains(driver).drag_and_drop_by_offset(driver.find_element_by_id('nc_1_n1z'),298,0).perform()
            pass

        if driver.current_url == login_url:
            error = driver.find_element_by_xpath("//p[@class='error']")
            if error.is_displayed():
                print('验证码')
                pass
            print('登录失败')

        cookies = driver.get_cookies()
        driver.quit()


        driver.find_element_by_xpath("//*[@id='J_SubmitStatic']").click()
        time.sleep(4)



        frame = driver.find_element_by_xpath('//iframe[@id="J_loginIframe"]')
        driver.switch_to.frame(frame)
        driver.find_element_by_id('J_Quick2Static').click()

        time.sleep(2)
        driver.find_element_by_id('TPL_username_1').click()
        driver.find_element_by_id('TPL_username_1').clear()
        driver.find_element_by_id('TPL_username_1').send_keys(username)
        time.sleep(2)
        driver.find_element_by_id('TPL_password_1').click()
        driver.find_element_by_id('TPL_password_1').clear()
        driver.find_element_by_id('TPL_password_1').send_keys(passwd)
        while True:
            try:
                #ActionChains(driver).drag_and_drop(driver.find_element_by_id('nc_1_n1z'), driver.find_element_by_id('J_Static2Quick')).perform()
                nano = driver.find_element_by_id('nc_1_n1z')
                if nano != None:
                    ActionChains(driver).drag_and_drop_by_offset(driver.find_element_by_id('nc_1_n1z'),298,0).perform()
                    if driver.current_url != login_url:
                        print('登录失败')
                        break

                    text=driver.find_element_by_xpath("//div[@id='nc_1__scale_text']/span").text

                    if text.text.startswith(u'请在下方输入验证码'):
                        continue

                    if text.text.startswith(u'请在下方'):
                        print('成功滑动')
                        break

                    if text.text.startswith(u'请点击'):
                        print('成功滑动')
                        break
                    if text.text.startswith(u'请按住'):
                        continue
            except Exception as e:
            #这里定位失败后的刷新按钮，重新加载滑块模块
                driver.find_element_by_xpath("//div[@id='havana_nco']/div/span/a").click()
                print(e)


            time.sleep(2)
            driver.find_element_by_id('J_SubmitStatic').click()
            driver.switch_to_default_content()

        cookies = driver.get_cookies()
        driver.quit()



    def sele_login(self, login_url, username, passwd):

        #firefox_profile = webdriver.FirefoxProfile(r'C:\Users\wanglongzhen\AppData\Roaming\Mozilla\Firefox\Profiles\9anudwvy.default')
        # driver = webdriver.Firefox(firefox_profile=firefox_profile)
        #driver = webdriver.PhantomJS()
        driver = webdriver.Firefox()
        driver.maximize_window()

        driver.get(login_url)

        driver.find_element_by_id('J_Quick2Static').click()

        time.sleep(2)
        driver.find_element_by_id('TPL_username_1').clear()
        driver.find_element_by_id('TPL_username_1').send_keys('wanglongzhen_2008')
        time.sleep(2)
        driver.find_element_by_id('TPL_password_1').clear()
        driver.find_element_by_id('TPL_password_1').send_keys('wlz9087881')
        while True:
            try:
                #ActionChains(driver).drag_and_drop(driver.find_element_by_id('nc_1_n1z'), driver.find_element_by_id('J_Static2Quick')).perform()
                nano = driver.find_element_by_id('nc_1_n1z')
                if nano != None:
                    ActionChains(driver).drag_and_drop_by_offset(driver.find_element_by_id('nc_1_n1z'),298,0).perform()
                    text=driver.find_element_by_xpath("//div[@id='nc_1__scale_text']/span")

                    if text.text.startswith(u'请在下方'):
                        print('成功滑动')
                        break
                    if text.text.startswith(u'请点击'):
                        print('成功滑动')
                        break
                    if text.text.startswith(u'请按住'):
                        continue
            except Exception as e:
            #这里定位失败后的刷新按钮，重新加载滑块模块
                driver.find_element_by_xpath("//div[@id='havana_nco']/div/span/a").click()
                print(e)


            time.sleep(2)
            driver.find_element_by_id('J_SubmitStatic').click()



        driver.quit()



        # #登录 支付宝
        # driver.find_element_by_id('J-input-user').click()
        # driver.find_element_by_id('J-input-user').send_keys('wanglongzhen_2008')
        # time.sleep(5)
        # driver.find_element_by_id('password_rsainput').send_keys('wlz9087881')
        # time.sleep(5)
        #
        #
        # driver.find_element_by_id('J-login-btn').click()
        # time.sleep(5)
        #
        #
        # #图片识别
        # driver.find_elements_by_id('J-checkcode-img')
        # soup = bs(driver.page_source)
        # img = soup.find('img', id = 'J-checkcode-img')
        # if img != None:
        #     img_href = img.get('src')
        #     with open('img.jpg', 'wb') as f:
        #         f.write(requests.get(img_href).content)
        #     img_id = raw_input("please input image code:")
        #     driver.find_element_by_id('J-input-checkcode').send_kyes(img_id)
        #
        #
        # #跳转
        # driver.get('https://shenghuo.alipay.com/send/payment/fill.htm?_pdType=adbhajcaccgejhgdaeih')
        # soup = bs(driver.page_source)
        # # driver.find_element_by_id('receiveNameAlert').click()
        #
        # time.sleep(10)
        # driver.find_element_by_id('ipt-search-key').click()
        # driver.find_element_by_id('ipt-search-key').send_keys('18260086180')
        # time.sleep(2)
        # driver.find_element_by_id('ipt-search-key').send_keys(Keys.TAB)
        #
        #
        # print driver.get_cookies()
        #
        # print soup
        # driver.find_elements_by_id('receiveNameAlert')
        # pass

    def login(self, login_url, username, passwd):

        self.r = requests.session()

        ret = self.r.get(login_url, headers = self.headers, cookies = self.r.cookies)

        soup = bs(ret.text, 'html.parser')
        # print soup

        # step 1 获取ctoken
        ctoken = None
        for cookie in self.r.cookies:
            if cookie.name == 'ctoken':
                ctoken = cookie.value

        if ctoken == None:
            return

        # step 2 获取图片验证码


        # step 3 登录


        # check_img = 'https://authzui.alipay.com/login/index.htm?seed=authlogin-showCheckCode-authzui&pg=https://authzui.alipay.com/login/index.htm?seed=authcenter-input-checkcode'
        # param_check_img_data = {
        #     'ref' : 'https://authzui.alipay.com/login/index.htm?seed=authlogin-showCheckCode-authzui',
        #     'pg' : 'https://authzui.alipay.com/login/index.htm?seed=authcenter-input-checkcode',
        #     'BIProfile' : 'clk',
        #     'r' : '0.7328615603166728',
        #     'v' : '1.1'
        # }

        #login
        verify_url = 'https://authzui.alipay.com/login/verifyCheckCode.json'
        check_code_data = {
            # 'checkCode' : check_code,
            'idPrefix' : '',
            'timestamp' : str(int(time.time() * 1000)),
            '_input_charset' : 'utf-8',
            'ctoken' : ctoken
        }

        ret = self.r.post(verify_url, check_code_data, headers = self.headers, cookies = self.r.cookies)

        soup = bs(ret.text, 'html.parser')
        print soup



def main():
    transfer_accounts = TransferAccounts()



if __name__ == '__main__':
    main()
    pass