# -*- coding:utf-8 -*-

"""
File Name: location_scraper.py
Version: 0.1
Description: 根据手机号，获取其归属地信息

Author: gonghao
Date: 2016/6/29 14:32
"""

import requests
from bs4 import BeautifulSoup as BSoup
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


def location_scrape(phone):
    """
    根据手机号，获取手机归属地
    """
    url = "http://www.ip138.com:8080/search.asp?mobile={phone}&action=mobile"
    res = requests.get(url.format(phone=phone))
    res.encoding = "gb2312"
    soup = BSoup(res.text, 'html.parser')
    location = soup.select(".tdc2")[1].text.replace(u"市", "").split(u"\xa0")

    if len(location) == 1:
        return [location[0], location[0]]
    elif location[1] == u"":
        return [location[0], location[0]]
    else:
        return location

if __name__ == '__main__':
    print ', '.join(location_scrape("18602132395"))
    print ', '.join(location_scrape("15157124594"))
    print ', '.join(location_scrape("18672845875"))
    print ', '.join(location_scrape("13500550128"))
    print ', '.join(location_scrape("18611088915"))
