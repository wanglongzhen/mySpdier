#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'test_utils'.py 
Description: utils模块的单元测试
Author: 'zhengyang' 
Date: '2016/11/1' '8:49'
"""

import datetime
import unittest
from mobile_shop_spider import utils


class TestUtils(unittest.TestCase):
    def test_get_date(self):
        self.assertEquals(utils.get_date(u"2016年9月01日"), "2016-09-01")
        self.assertEquals(utils.get_date(u"2016年10月01日"), "2016-10-01")
        self.assertEquals(utils.get_date(None), "")
        self.assertEquals(utils.get_date(u"2016年10月"), "2016-10")
        self.assertEquals(utils.get_date(u"2016年"), "2016")
        self.assertEquals(utils.get_date(u"2016"), "")

    def test_get_state(self):
        self.assertEquals(utils.get_state(u"正常"), 0)
        self.assertEquals(utils.get_state("00"), 0)
        self.assertEquals(utils.get_state(None), -1)
        self.assertEquals(utils.get_state("Undefined"), -1)

    def test_get_value(self):
        self.assertEquals(utils.get_value(u"￥17.26"), 1726)
        self.assertEquals(utils.get_value("0.1"), 10)
        self.assertEquals(utils.get_value(None), 0)
        self.assertEquals(utils.get_value("Undefined"), 0)

    def test_get_duration(self):
        self.assertEquals(utils.get_duration(u"1小时1分1秒"), 3661)
        self.assertEquals(utils.get_duration("01:01:01"), 3661)
        self.assertEquals(utils.get_duration(None), 0)
        self.assertEquals(utils.get_duration("Undefined"), 0)

    def test_get_open_time(self):
        current_day = datetime.datetime.strptime("2016-11-01", "%Y-%m-%d").date()
        self.assertEquals(utils.get_open_time(u"1个月", current_day), "2016-10-02")

    def test_get_jquery_detail(self):
        resp = u"jQuery18305637221474059924_1477639014937($wanted_data)"
        self.assertEquals(utils.get_jquery_detail(resp), "$wanted_data")

        resp = u"jQuery18305637221474059924_1477639014937((())))"
        self.assertEquals(utils.get_jquery_detail(resp), "(()))")

        resp = u"jQuery18305637221474059924_1477639014937([\\//])"
        self.assertEquals(utils.get_jquery_detail(resp), "[\\//]")

        resp = u"""jQuery18305637221474059924_1477639014937({"abc":"anc"})"""
        self.assertEquals(utils.get_jquery_detail(resp), """{"abc":"anc"}""")

        resp = "this is wrong resp"
        with self.assertRaises(ValueError):
            utils.get_jquery_detail(resp)

    def test_get_province_code(self):
        with self.assertRaises(ValueError):
            utils.get_province_code("abc")

        self.assertEquals(utils.get_province_code(220), u"天津")
        self.assertEquals(utils.get_province_code("220"), u"天津")

    def test_get_msg_type(self):
        self.assertEquals(utils.get_msg_type(u"短信"), "SMS")
        self.assertEquals(utils.get_msg_type(u"短彩信"), "SMS")
        self.assertEquals(utils.get_msg_type(u"彩信"), "MMS")

if __name__ == '__main__':
    unittest.main()