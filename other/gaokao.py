# -*- coding:utf-8 -*-
"""
File Name : 'gaokao'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/8/3' '10:31'
"""



import os
import time
import traceback
from bs4 import BeautifulSoup as bs
import requests
import cookielib
import sys
import  re
reload(sys)
sys.setdefaultencoding( "utf-8" )


def writeFailedDetailUrl(data, path = 'gaokao/gaokao.txt'):

    if os.path.exists(os.path.dirname(path)):

        f = open(path, 'w')
    else:
        os.makedirs(os.path.dirname(path))
        f = open(path, 'w')

    f.write(data + "\n")

    f.close()


def main():
    pass
    r = requests.get('http://edu.sina.com.cn/gaokao/baoming/')
    r.encoding = 'gb2312'
    soup = bs(r.text, 'html.parser')

    file_data = ''
    data_items = [data_item for data_item in soup.find('tbody').find_all('tr')]
    for item in data_items:

        list = [data.get_text() for data in item.find_all('td')]
        line = ''
        for l in list:
            # print re.sub('[^\d\.]', '', l.encode('utf-8'))
            line += re.sub('[^\d\.]', '', l.encode('utf-8')) + "\t"
        print line
        file_data += line + "\n"


    writeFailedDetailUrl(file_data)

if __name__ == '__main__':
    # main()