# -*- coding:utf-8 -*-
"""
File Name : 'warpper'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/8/4' '14:05'
"""

import os


def log(text):
    def decorator(func):
        def warpper(*args, **kwargs):
            print ('%s %s():' % (text, func.__name__))
            return func(*args, **kwargs)
        return warpper
    return decorator

@log('text')
def now():
    print ('2016-3-25')


now()





