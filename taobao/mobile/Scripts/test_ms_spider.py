#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'test_ms_spider'.py 
Description: 移动商城爬虫数据解析函数的单元测试
Author: 'zhengyang' 
Date: '2016/10/31' '16:17'
"""
import unittest
import json
from mobile_shop_spider import MobileShopSpider


class TestMobileShopSpider(unittest.TestCase):

    def test_parse_package_usage(self):
        # sample 1 江苏
        resp = u"""{"data":[{"arr":[{"remark":null,"mealName":"1元包本地主叫200分钟(09版集团套餐)","planId":"2000001586","resInfos":[{"remark":null,"resName":null,"resCode":"01","isMultiTerm":null,"secResInfos":[{"remark":null,"resConInfo":{"remark":null,"totalMeal":"200","useMeal":"0","balMeal":"200","unit":"01","validDate":"20161028151639"},"resConCode":null,"resConName":"语音资源"}]}],"mealInfoUps":[]},{"remark":null,"mealName":"动感地带游戏套餐","planId":"2000002064","resInfos":[{"remark":null,"resName":null,"resCode":"02","isMultiTerm":null,"secResInfos":[{"remark":null,"resConInfo":{"remark":null,"totalMeal":"200","useMeal":"10","balMeal":"190","unit":"02","validDate":"20161028151639"},"resConCode":null,"resConName":"短信资源"}]},{"remark":null,"resName":null,"resCode":"04","isMultiTerm":"1","secResInfos":[{"remark":null,"resConInfo":{"remark":null,"totalMeal":"61440","useMeal":"61440","balMeal":"0","unit":"03","validDate":"20161028151639"},"resConCode":null,"resConName":"国内2/3/4G融合流量上月结转"},{"remark":null,"resConInfo":{"remark":null,"totalMeal":"61440","useMeal":"9628","balMeal":"51812","unit":"03","validDate":"20161028151640"},"resConCode":null,"resConName":"国内2/3/4G融合流量"}]}],"mealInfoUps":[]},{"remark":null,"mealName":"亲情号码组合（1元月功能费）","planId":"2000004907","resInfos":[{"remark":null,"resName":null,"resCode":"01","isMultiTerm":null,"secResInfos":[{"remark":null,"resConInfo":{"remark":null,"totalMeal":"500","useMeal":"13","balMeal":"487","unit":"01","validDate":"20161028151640"},"resConCode":null,"resConName":"语音资源"}]}],"mealInfoUps":[]}],"type":"1"}],"retCode":"000000","retMsg":"成功","sOperTime":"20161028151639"}"""
        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        package_usage = ms_spider.parse_package_usage(resp)
        self.assertEquals(package_usage["task_id"], "ms_test")
        self.assertEquals(package_usage["mobile"], "12345678911")
        self.assertEquals(len(package_usage["items"]), 3)
        self.assertTrue(u"1元包本地主叫200分钟(09版集团套餐)"in [item["item"] for item in package_usage["items"]])
        self.assertEquals(package_usage["items"][0]["item"], u"1元包本地主叫200分钟(09版集团套餐)")
        self.assertEquals(package_usage["items"][0]["total"], "200")
        self.assertEquals(package_usage["items"][0]["used"], "0")
        self.assertEquals(package_usage["items"][0]["unit"], "")

    def test_parse_recharge(self):
        # smaple 江苏
        resp = u"""{"data":[{"payDate":"20160527121401","payFee":"50.00","payChannel":"09","payAddr":null,"payFlag":null,"payType":"05","payTypeName":"积分支付","payStaffCode":null},{"payDate":"20160501084840","payFee":"40.00","payChannel":"09","payAddr":null,"payFlag":null,"payType":"12","payTypeName":"缴费","payStaffCode":null}],"retCode":"000000","retMsg":"成功","sOperTime":"20161028151719"}"""
        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        recharge_list = list(ms_spider.parse_recharge(resp))
        self.assertEquals(len(recharge_list), 2)

        recharge_0 = recharge_list[0]
        self.assertEquals(recharge_0["recharge_time"], "2016-05-27")
        self.assertEquals(recharge_0["type"], u"积分支付")
        self.assertEquals(recharge_0["amount"], 5000)

    def test_parse_sms(self):
        # sample 1
        with open("test_data/sms_201605") as f:
            resp = f.read()

        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        sms_list = list(ms_spider.parse_sms_by_month(resp, ["2016-05-01", "2016-05-31", "201605"]))
        self.assertEquals(len(sms_list), 54)

        sms = sms_list[0]
        self.assertEquals(sms["task_id"], "ms_test")
        self.assertEquals(sms["mobile"], "12345678911")
        self.assertEquals(sms["time"], "2016-05-02 20:27:34")

        self.assertEquals(sms["peer_number"], "10086")
        self.assertEquals(sms["location"], u"内地")
        self.assertEquals(sms["send_type"], "RECEIVE")

        self.assertEquals(sms["msg_type"], "SMS")
        self.assertEquals(sms["service_name"], "")
        self.assertEquals(sms["fee"], 0)

        # sample 安徽 安徽的通信地点有可能是 “梦网短信” “网内短信” 这种
        resp = u"""jQuery18307625997071979864_1478653550185({"data":[{"remark":null,"startTime":"2016-09-02 13:44:40","commPlac":"梦网短信","anotherNm":"10658104","infoType":"梦网短信","busiName":"--","meal":"--","commFee":"0.00","commMode":"发送"},{"remark":null,"startTime":"2016-09-12 14:05:47","commPlac":"梦网短信","anotherNm":"10658104","infoType":"梦网短信","busiName":"--","meal":"--","commFee":"0.00","commMode":"发送"},{"remark":null,"startTime":"2016-09-13 09:39:23","commPlac":"梦网短信","anotherNm":"10658104","infoType":"梦网短信","busiName":"--","meal":"--","commFee":"0.00","commMode":"发送"},{"remark":null,"startTime":"2016-09-13 09:40:13","commPlac":"网内短信","anotherNm":"15034152437","infoType":"网内短信","busiName":"短信","meal":"--","commFee":"0.10","commMode":"发送"}],"totalNum":4,"startDate":"20160901","endDate":"20160930","curCuror":1,"retCode":"000000","retMsg":"get data from cache success","sOperTime":"20161109090324"})"""
        ms_spider = MobileShopSpider(task_id="anhui", phone="12345678911", password="123456")
        sms_list = list(ms_spider.parse_sms_by_month(resp, "201609"))

        sms = sms_list[0]
        self.assertEquals(sms["task_id"], "anhui")
        self.assertEquals(sms["mobile"], "12345678911")
        self.assertEquals(sms["time"], "2016-09-02 13:44:40")

        self.assertEquals(sms["peer_number"], "10658104")
        self.assertEquals(sms["location"], u"梦网短信")
        self.assertEquals(sms["send_type"], "SEND")

        self.assertEquals(sms["msg_type"], "SMS")
        self.assertEquals(sms["service_name"], "--")
        self.assertEquals(sms["fee"], 0)

        # sample 广州
        resp = u"""jQuery18303435858610724538_1478655375423({"data":[{"remark":null,"startTime":"09-18 14:07:37","commPlac":"内地","anotherNm":"106581043","infoType":"短信","busiName":"99901348","meal":"4G流量王","commFee":"0.00","commMode":"发送"},{"remark":null,"startTime":"09-19 09:44:39","commPlac":"内地","anotherNm":"106581043","infoType":"短信","busiName":"99901348","meal":"4G流量王","commFee":"0.00","commMode":"发送"},{"remark":null,"startTime":"09-20 10:33:01","commPlac":"内地","anotherNm":"106581043","infoType":"短信","busiName":"99901348","meal":"4G流量王","commFee":"0.00","commMode":"发送"},{"remark":null,"startTime":"09-28 14:12:31","commPlac":"内地","anotherNm":"-","infoType":"短信","busiName":"中国移动-积分计划统一平台","meal":"4G流量王","commFee":"0.00","commMode":"接受"},{"remark":null,"startTime":"09-28 14:12:31","commPlac":"内地","anotherNm":"-","infoType":"短信","busiName":"中国移动-积分计划统一平台","meal":"4G流量王","commFee":"0.00","commMode":"接受"}],"totalNum":5,"startDate":"20160901","endDate":"20160930","curCuror":1,"retCode":"000000","retMsg":"get data from cache success","sOperTime":"20161109094317"})"""
        ms_spider = MobileShopSpider(task_id="guangzhou", phone="12345678911", password="123456")
        sms_list = list(ms_spider.parse_sms_by_month(resp, "201609"))

        sms = sms_list[3]
        self.assertEquals(sms["task_id"], "guangzhou")
        self.assertEquals(sms["mobile"], "12345678911")
        self.assertEquals(sms["time"], "2016-09-28 14:12:31")

        self.assertEquals(sms["peer_number"], "-")
        self.assertEquals(sms["location"], u"内地")
        self.assertEquals(sms["send_type"], "RECEIVE")

        self.assertEquals(sms["msg_type"], "SMS")
        self.assertEquals(sms["service_name"], u"中国移动-积分计划统一平台")
        self.assertEquals(sms["fee"], 0)

    def test_parse_call(self):
        # sample 江苏
        with open("test_data/call_201605") as f:
            resp = f.read()

        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        call_list = list(ms_spider.parse_call_by_month(resp, ["2016-05-01", "2016-05-31", "201605"]))
        self.assertEquals(len(call_list), 84)

        call_list_0 = call_list[0]
        self.assertEquals(call_list_0["task_id"], "ms_test")
        self.assertEquals(call_list_0["mobile"], "12345678911")
        self.assertEquals(call_list_0["time"], "2016-05-01 06:19:29")

        self.assertEquals(call_list_0["peer_number"], "15952011561")
        self.assertEquals(call_list_0["location"], u"南京")
        self.assertEquals(call_list_0["location_type"], u"本地(非漫游、被叫)")

        self.assertEquals(call_list_0["dial_type"], "DIAL")
        self.assertEquals(call_list_0["duration"], 67)
        self.assertEquals(call_list_0["fee"], 0)

        # sample 黑龙江
        # 黑龙江通话记录会有通话地点、通信方式、对方号码等为"--"的数据
        resp = u"""jQuery18306770560556909955_1478597432592({"data":[{"remark":null,"startTime":"10-31 23:59:59","commPlac":"--","commMode":"--","anotherNm":"--","commTime":"--","commType":"--","mealFavorable":"本地通话","commFee":"1"},{"remark":null,"startTime":"10-31 23:59:59","commPlac":"--","commMode":"--","anotherNm":"--","commTime":"--","commType":"--","mealFavorable":"本地通话","commFee":"8"}],"totalNum":2,"startDate":"20161001","endDate":"20151231","curCuror":1,"retCode":"000000","retMsg":"get data from cache success","sOperTime":"20161108172758"})"""
        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        call_list = list(ms_spider.parse_call_by_month(resp, "201610"))
        self.assertEquals(len(call_list), 2)

        call_list_0 = call_list[0]
        self.assertEquals(call_list_0["task_id"], "ms_test")
        self.assertEquals(call_list_0["mobile"], "12345678911")
        self.assertEquals(call_list_0["time"], "2016-10-31 23:59:59")

        self.assertEquals(call_list_0["peer_number"], "--")
        self.assertEquals(call_list_0["location"], u"--")
        self.assertEquals(call_list_0["location_type"], u"--")

        self.assertEquals(call_list_0["dial_type"], "DIALED")
        self.assertEquals(call_list_0["duration"], 0)




    def test_parse_bill(self):
        # sample 江苏
        resp = u"""{"data":[{"remark":null,"billMonth":"201611","billStartDate":"20161101","billEndDate":"20161130","billFee":"0.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201610","billStartDate":"20161001","billEndDate":"20161031","billFee":"78.30","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"29.00","billMaterialInfos":[{"remark":null,"itemName":"来电显示","itemValue":"5.00"},{"remark":null,"itemName":"动感易查询","itemValue":"1.00"},{"remark":null,"itemName":"来电提醒(短信呼)","itemValue":"1.00"},{"remark":null,"itemName":"集团V网（同事网）套餐费","itemValue":"1.00"},{"remark":null,"itemName":"亲情号码套餐费","itemValue":"1.00"},{"remark":null,"itemName":"动感地带游戏套餐费","itemValue":"20.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"9.30","billMaterialInfos":[{"remark":null,"itemName":"本地主叫通话费","itemValue":"7.20"},{"remark":null,"itemName":"移动400业务","itemValue":"2.10"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"40.00","billMaterialInfos":[{"remark":null,"itemName":"宽带包时套餐费","itemValue":"40.00"}]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201609","billStartDate":"20160901","billEndDate":"20160930","billFee":"73.50","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"29.00","billMaterialInfos":[{"remark":null,"itemName":"来电显示","itemValue":"5.00"},{"remark":null,"itemName":"动感易查询","itemValue":"1.00"},{"remark":null,"itemName":"来电提醒(短信呼)","itemValue":"1.00"},{"remark":null,"itemName":"集团V网（同事网）套餐费","itemValue":"1.00"},{"remark":null,"itemName":"亲情号码套餐费","itemValue":"1.00"},{"remark":null,"itemName":"动感地带游戏套餐费","itemValue":"20.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"4.50","billMaterialInfos":[{"remark":null,"itemName":"本地主叫通话费","itemValue":"4.50"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"40.00","billMaterialInfos":[{"remark":null,"itemName":"宽带包时套餐费","itemValue":"40.00"}]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201608","billStartDate":"20160801","billEndDate":"20160831","billFee":"72.30","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"29.00","billMaterialInfos":[{"remark":null,"itemName":"来电显示","itemValue":"5.00"},{"remark":null,"itemName":"动感易查询","itemValue":"1.00"},{"remark":null,"itemName":"来电提醒(短信呼)","itemValue":"1.00"},{"remark":null,"itemName":"集团V网（同事网）套餐费","itemValue":"1.00"},{"remark":null,"itemName":"亲情号码套餐费","itemValue":"1.00"},{"remark":null,"itemName":"动感地带游戏套餐费","itemValue":"20.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"3.30","billMaterialInfos":[{"remark":null,"itemName":"本地主叫通话费","itemValue":"2.90"},{"remark":null,"itemName":"移动400业务","itemValue":"0.40"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"40.00","billMaterialInfos":[{"remark":null,"itemName":"宽带包时套餐费","itemValue":"40.00"}]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201607","billStartDate":"20160701","billEndDate":"20160731","billFee":"75.30","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"29.00","billMaterialInfos":[{"remark":null,"itemName":"来电显示","itemValue":"5.00"},{"remark":null,"itemName":"动感易查询","itemValue":"1.00"},{"remark":null,"itemName":"来电提醒(短信呼)","itemValue":"1.00"},{"remark":null,"itemName":"集团V网（同事网）套餐费","itemValue":"1.00"},{"remark":null,"itemName":"亲情号码套餐费","itemValue":"1.00"},{"remark":null,"itemName":"动感地带游戏套餐费","itemValue":"20.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"6.30","billMaterialInfos":[{"remark":null,"itemName":"本地主叫通话费","itemValue":"6.20"},{"remark":null,"itemName":"移动400业务","itemValue":"0.10"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"40.00","billMaterialInfos":[{"remark":null,"itemName":"宽带包时套餐费","itemValue":"40.00"}]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201606","billStartDate":"20160601","billEndDate":"20160630","billFee":"96.40","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"49.00","billMaterialInfos":[{"remark":null,"itemName":"来电显示","itemValue":"5.00"},{"remark":null,"itemName":"动感易查询","itemValue":"1.00"},{"remark":null,"itemName":"来电提醒(短信呼)","itemValue":"1.00"},{"remark":null,"itemName":"集团V网（同事网）套餐费","itemValue":"1.00"},{"remark":null,"itemName":"亲情号码套餐费","itemValue":"1.00"},{"remark":null,"itemName":"动感地带游戏套餐费","itemValue":"20.00"},{"remark":null,"itemName":"4G流量可选包","itemValue":"20.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"7.40","billMaterialInfos":[{"remark":null,"itemName":"本地主叫通话费","itemValue":"6.30"},{"remark":null,"itemName":"移动400业务","itemValue":"1.10"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"40.00","billMaterialInfos":[{"remark":null,"itemName":"宽带包时套餐费","itemValue":"40.00"}]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]}],"retCode":"000000","retMsg":"业务异常","sOperTime":"20161101090958"}"""

        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        bill_list = list(ms_spider.parse_bill(resp))
        self.assertEquals(len(bill_list), 5)

        bill_list_0 = bill_list[0]
        self.assertEquals(bill_list_0["task_id"], "ms_test")
        self.assertEquals(bill_list_0["mobile"], "12345678911")
        self.assertEquals(bill_list_0["bill_month"], "2016-10")
        self.assertEquals(bill_list_0["bill_start_date"], "2016-10-01")
        self.assertEquals(bill_list_0["bill_end_date"], "2016-10-31")

        self.assertEquals(bill_list_0["base_fee"], 2900)
        self.assertEquals(bill_list_0["extra_service_fee"], 0)
        self.assertEquals(bill_list_0["voice_fee"], 930)
        self.assertEquals(bill_list_0["sms_fee"], 0)
        self.assertEquals(bill_list_0["web_fee"], 0)

        self.assertEquals(bill_list_0["extra_fee"], 0)
        self.assertEquals(bill_list_0["discount"], 4000)
        self.assertEquals(bill_list_0["total_fee"], 7830)
        self.assertEquals(bill_list_0["extra_discount"], 0)
        self.assertEquals(bill_list_0["actual_fee"], 3830)

        self.assertEquals(bill_list_0["paid_fee"], 0)
        self.assertEquals(bill_list_0["unpaid_fee"], 0)
        self.assertEquals(bill_list_0["point"], -1)
        self.assertEquals(bill_list_0["last_point"], -1)
        self.assertEquals(bill_list_0["related_mobiles"], list())

        self.assertEquals(bill_list_0["notes"], "")

        # sample 黑龙江
        # 黑龙江没有账单的月份bill_start_date，bill_end_date为空字符串，
        # 其它大部分省份没有账单的月份bill_start_date，bill_end_date为月初月末日期
        resp = u"""{"data":[{"remark":null,"billMonth":"201611","billStartDate":"20161101","billEndDate":"20161130","billFee":"4.34","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"2.31","billMaterialInfos":[]},{"remark":null,"billEntriy":"02","billEntriyValue":"2.03","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201610","billStartDate":"20161001","billEndDate":"20161031","billFee":"19.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"18.00","billMaterialInfos":[{"remark":null,"itemName":"移动数据流量(隐藏)","itemValue":"15.99"},{"remark":null,"itemName":"本地通话","itemValue":"2.01"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"1.00","billMaterialInfos":[{"remark":null,"itemName":"本地通话","itemValue":"1.00"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201609","billStartDate":"20160901","billEndDate":"20160930","billFee":"19.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"18.00","billMaterialInfos":[{"remark":null,"itemName":"移动数据流量(隐藏)","itemValue":"15.99"},{"remark":null,"itemName":"本地通话","itemValue":"2.01"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"1.00","billMaterialInfos":[{"remark":null,"itemName":"本地通话","itemValue":"1.00"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201608","billStartDate":"20160801","billEndDate":"20160831","billFee":"26.28","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"26.01","billMaterialInfos":[{"remark":null,"itemName":"本地通话","itemValue":"3.25"},{"remark":null,"itemName":"gprs套餐功能费","itemValue":"22.76"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.27","billMaterialInfos":[{"remark":null,"itemName":"本地通话","itemValue":"0.27"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201607","billStartDate":null,"billEndDate":null,"billFee":"-0","billMaterials":[]},{"remark":null,"billMonth":"201606","billStartDate":null,"billEndDate":null,"billFee":"-0","billMaterials":[]}],"retCode":"000000","retMsg":"success","sOperTime":"20161108172152"}"""
        ms_spider = MobileShopSpider(task_id="heilongjiang", phone="12345678911", password="123456")
        bill_list = list(ms_spider.parse_bill(resp))
        self.assertEquals(len(bill_list), 5)

        bill_list_0 = bill_list[-1]
        self.assertEquals(bill_list_0["bill_month"], "2016-06")
        self.assertEquals(bill_list_0["bill_start_date"], "")
        self.assertEquals(bill_list_0["bill_end_date"], "")

        # sample 山西
        resp = u"""{"data":[{"remark":null,"billMonth":"201611","billStartDate":"20161101","billEndDate":"20161130","billFee":"16.57","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"16.57","billMaterialInfos":[{"remark":null,"itemName":"移动数据流量月费分摊","itemValue":"16.57"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201610","billStartDate":"20161001","billEndDate":"20161031","billFee":"18.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"18.00","billMaterialInfos":[{"remark":null,"itemName":"移动数据流量月费分摊","itemValue":"18.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201609","billStartDate":"20160901","billEndDate":"20160930","billFee":"18.10","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"18.00","billMaterialInfos":[{"remark":null,"itemName":"移动数据流量月费分摊","itemValue":"18.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.10","billMaterialInfos":[{"remark":null,"itemName":"国内漫游基本费","itemValue":"0.10"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201608","billStartDate":"20160801","billEndDate":"20160831","billFee":"4.73","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"4.73","billMaterialInfos":[{"remark":null,"itemName":"移动数据流量月费分摊","itemValue":"4.73"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201607","billStartDate":null,"billEndDate":null,"billFee":"-0","billMaterials":[]},{"remark":null,"billMonth":"201606","billStartDate":null,"billEndDate":null,"billFee":"-0","billMaterials":[]}],"retCode":"000000","retMsg":"TradeOK","sOperTime":"20161128160416"}"""
        ms_spider = MobileShopSpider(task_id="heilongjiang", phone="12345678911", password="123456")
        bill_list = list(ms_spider.parse_bill(resp))
        self.assertEquals(len(bill_list), 5)

        bill_list_0 = bill_list[0]
        self.assertEquals(bill_list_0["bill_month"], "2016-10")
        self.assertEquals(bill_list_0["bill_start_date"], "2016-10-01")
        self.assertEquals(bill_list_0["bill_end_date"], "2016-10-31")

        # sample 湖南
        resp = u"""{"data":[{"remark":null,"billMonth":"201611","billStartDate":"20161101","billEndDate":"20161130","billFee":"16.52","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"16.52","billMaterialInfos":[]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201610","billStartDate":"20161001","billEndDate":"20161031","billFee":"18.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"18.00","billMaterialInfos":[{"remark":null,"itemName":"总费用优惠费","itemValue":"18.00"}]}]},{"remark":null,"billMonth":"201609","billStartDate":"20160901","billEndDate":"20160930","billFee":"18.57","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"18.00","billMaterialInfos":[{"remark":null,"itemName":"4G飞享套餐18元档2016升级版(语音套餐)","itemValue":"8.00"},{"remark":null,"itemName":"4G飞享套餐18元档2016升级版(流量套餐)","itemValue":"10.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.57","billMaterialInfos":[{"remark":null,"itemName":"省际漫游费","itemValue":"0.57"}]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201608","billStartDate":"20160801","billEndDate":"20160831","billFee":"18.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"12.08","billMaterialInfos":[{"remark":null,"itemName":"4G飞享套餐18元档2016升级版(语音套餐)","itemValue":"2.08"},{"remark":null,"itemName":"4G飞享套餐18元档2016升级版(流量套餐)","itemValue":"10.00"}]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"5.92","billMaterialInfos":[{"remark":null,"itemName":"保底消费额帐目项","itemValue":"5.92"}]}]},{"remark":null,"billMonth":"201607","billStartDate":"20160701","billEndDate":"20160731","billFee":"0.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]},{"remark":null,"billMonth":"201606","billStartDate":"20160601","billEndDate":"20160630","billFee":"0.00","billMaterials":[{"remark":null,"billEntriy":"01","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"02","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"03","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"04","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"05","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"06","billEntriyValue":"0.00","billMaterialInfos":[]},{"remark":null,"billEntriy":"09","billEntriyValue":"0.00","billMaterialInfos":[]}]}],"retCode":"000000","retMsg":"success","sOperTime":"20161129165836"}"""
        ms_spider = MobileShopSpider(task_id="hunan", phone="12345678911", password="123456")
        bill_list = list(ms_spider.parse_bill(resp))
        self.assertEquals(len(bill_list), 5)

        bill_list_0 = bill_list[0]
        self.assertEquals(bill_list_0["bill_month"], "2016-10")
        self.assertEquals(bill_list_0["bill_start_date"], "2016-10-01")
        self.assertEquals(bill_list_0["bill_end_date"], "2016-10-31")
        self.assertEquals(bill_list_0["total_fee"], 1800)

        bill = bill_list[1]
        self.assertEquals(bill["bill_month"], "2016-09")
        self.assertEquals(bill["bill_start_date"], "2016-09-01")
        self.assertEquals(bill["bill_end_date"], "2016-09-30")
        self.assertEquals(bill["total_fee"], 1856)

    def test_parse_basic(self):
        # sample 1 江苏
        result = u"""{"data":{"remark":null,"name":"xx健","brand":"01","level":"100","status":"00","inNetDate":"20160828155042","netAge":"3个月","email":"","address":"西安市蓝田县华胥镇张家斜村第三村民小组","zipCode":"730000","contactNum":"18794224550","starLevel":"0","starScore":"0","starTime":null,"realNameInfo":"3","vipInfo":null},"retCode":"000000","retMsg":"成功","sOperTime":"20161103111435"}"""
        result_2 = u"""{"data":{"remark":null,"realFee":"19.80","curFee":"38.10","curFeeTotal":"57.90","oweFee":"0.00"},"retCode":"000000","retMsg":"成功","sOperTime":"20161103111640"}"""
        result_4 = u"""{"data":{"remark":null,"prov_cd":"931","id_area_cd":"0931","id_name_cd":"兰州","msisdn_area_id":null,"imsi_type":null,"effc_tm":null,"expired_tm":null,"num_type":"0"},"retCode":"000000","retMsg":"ok","sOperTime":null}"""
        result_3 = u"""{"data":{"remark":null,"custInfoQryOut":{"remark":null,"name":"xx健","brand":"01","level":"100","status":"00","inNetDate":"20160828155042","netAge":"3个月","email":"","address":"西安市蓝田县华胥镇张家斜村第三村民小组","zipCode":"730000","contactNum":"18794224550","starLevel":"0","starScore":"0","starTime":null,"realNameInfo":"3","vipInfo":null},"curPlanQryOut":{"remark":null,"brandId":"1","brandName":"全球通","curPlanId":"999393","curPlanName":"28元4G飞享套餐","nextPlanId":"999393","nextPlanName":"28元4G飞享套餐","startTime":null,"endTime":null},"sysTime":"20161103112112"},"retCode":"000000","retMsg":"成功,成功","sOperTime":"20161103112112"}"""

        ms_spider = MobileShopSpider(task_id="ms_test", phone="12345678911", password="123456")
        basic = ms_spider.parse_basic(result, result_2, result_3, result_4)

        self.assertEquals(basic["task_id"], "ms_test")
        self.assertEquals(basic["mobile"], "12345678911")
        self.assertEquals(basic["name"], u"xx健")

        self.assertEquals(basic["carrier"], "CHINA_MOBILE")
        self.assertEquals(basic["province"], u"甘肃")
        self.assertEquals(basic["city"], u"兰州")

        self.assertEquals(basic["open_time"], "2016-08-28")
        self.assertEquals(basic["level"], "100")
        self.assertEquals(basic["package_name"], "28元4G飞享套餐")

        self.assertEquals(basic["state"], 0)
        self.assertEquals(basic["available_balance"], 3810)

        # sample 陕西 13649258904
        result = u"""{"data":{"remark":null,"name":"赵*卓","brand":"09","level":"100","status":"00","inNetDate":"20160824141620","netAge":"3个月","email":"","address":"西安市雁塔区崇业路四十五号1号楼2单元3层1号","zipCode":"650000","contactNum":"","starLevel":"0","starScore":"0","starTime":"20501231","realNameInfo":"2","vipInfo":null},"retCode":"000000","retMsg":"成功","sOperTime":"20161107151833"}"""
        result_2 = u"""{"data":{"remark":null,"realFee":"4.14","curFee":"55.03","curFeeTotal":"59.17","oweFee":"0.00"},"retCode":"000000","retMsg":"TradeOK","sOperTime":"20161107145624"}"""
        result_3 = u"""{"data":{"remark":null,"custInfoQryOut":{"remark":null,"name":"赵*卓","brand":"09","level":"100","status":"00","inNetDate":"20160824141620","netAge":"3个月","email":"","address":"西安市雁塔区崇业路四十五号1号楼2单元3层1号","zipCode":"650000","contactNum":"","starLevel":"0","starScore":"0","starTime":"20501231","realNameInfo":"2","vipInfo":null},"curPlanQryOut":{"remark":null,"brandId":"01","brandName":"全球通","curPlanId":"99110149","curPlanName":"","nextPlanId":"99110149","nextPlanName":"4G飞享18元套餐(新版)","startTime":null,"endTime":null},"sysTime":"20161107145624"},"retCode":"000000","retMsg":"成功,成功","sOperTime":"20161107145624"}"""
        result_4 = u"""{"data":{"remark":null,"prov_cd":"290","id_area_cd":"029","id_name_cd":"西安","msisdn_area_id":null,"imsi_type":null,"effc_tm":null,"expired_tm":null,"num_type":"0"},"retCode":"000000","retMsg":"ok","sOperTime":null}"""
        basic = ms_spider.parse_basic(resp=result, resp_2=result_2, resp_3=result_3, resp_4=result_4)
        self.assertEquals(basic["province"], u"陕西")
        self.assertEquals(basic["city"], u"西安")
        self.assertEquals(basic["package_name"], u"4G飞享18元套餐(新版)")
        self.assertEquals(basic["state"], 0)
        self.assertEquals(basic["available_balance"], 5503)


if __name__ == '__main__':
    unittest.main()



