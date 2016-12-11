#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'models'.py
Description: 移动爬虫mongodb数据库模型
Author: 'zhengyang'
Date: '2016/9/21' '14:10'
"""
import mongoengine
from mongoengine import Document, StringField, IntField, \
    DateTimeField, ListField, EmbeddedDocumentField, EmbeddedDocument


class Basic(Document):
    """账号基本信息 basic"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    name = StringField(required=True)
    carrier = StringField(required=True)
    province = StringField(required=True)
    city = StringField(required=True, default="")
    open_time = StringField(required=True, default="")
    level = StringField(required=True, default="")
    package_name = StringField(required=True, default="")
    state = IntField(required=True, default=-1)
    available_balance = IntField(required=True, default=0)
    last_modify_time = StringField(required=True)
    scrape_dt = StringField(required=True)


class Bill(Document):
    """账号账单记录 bill"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    bill_month = StringField(required=True)
    bill_start_date = StringField(required=True)
    bill_end_date = StringField(required=True)
    base_fee = IntField(required=True)
    extra_service_fee = IntField(required=True)
    voice_fee = IntField(required=True)
    sms_fee = IntField(required=True)
    web_fee = IntField(required=True)
    extra_fee = IntField(required=True)
    total_fee = IntField(required=True)
    discount = IntField(required=True)
    extra_discount = IntField(required=True)
    actual_fee = IntField(required=True)
    paid_fee = IntField(required=True)
    unpaid_fee = IntField(required=True)
    point = IntField(required=True)
    last_point = IntField(required=True)
    related_mobiles = ListField(required=False)
    notes = StringField(required=True)


class Call(Document):
    """账号通话详情 call"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    time = StringField(required=True)
    peer_number = StringField(required=True)
    location = StringField(required=True)
    location_type = StringField(required=True)
    duration = IntField(required=True)
    dial_type = StringField(required=True)
    fee = IntField(required=True)


class PackageItem(EmbeddedDocument):
    item = StringField(required=False)
    total = StringField(required=False)
    used = StringField(required=False)
    unit = StringField(required=False)


class PackageUsage(Document):
    """账号套餐使用记录 package_usage"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    items = ListField(EmbeddedDocumentField(PackageItem))
    bill_month = StringField(required=True)
    bill_start_date = StringField(required=True)
    bill_end_date = StringField(required=True)


class Recharge(Document):
    """账号充值记录 recharge"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    recharge_time = StringField(required=True)
    amount = IntField(required=True)
    type = StringField(required=True)


class Sms(Document):
    """短信通话详情 sms"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    time = StringField(required=True)
    peer_number = StringField(required=True)
    location = StringField(required=True)
    send_type = StringField(required=True)
    msg_type = StringField(required=True)
    service_name = StringField(required=False, default="")
    fee = IntField(required=True)


class Status(Document):
    """账号爬取状态 status"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    status = StringField(required=True)
    scrape_dt = StringField(required=True)


class TaskReport(Document):
    """生成的各项报告 task_report"""
    task_id = StringField(required=True)
    mobile = StringField(required=True)
    report = StringField(required=True)
    scrape_dt = StringField(required=True)

if __name__ == "__main__":
    # example
    bill = Bill()
    bill["task_id"] = "1001"
    bill["mobile"] = "13866668888"
    print(bill["task_id"], bill["mobile"])

    mongoengine.connect("cmcc_web", host='99.48.58.22',username='test', password='test')
    # tr = Status(task_id="123", mobile="123456", status="1", scrape_dt="20161001")
    # tr.save()

    print Status.objects(mobile="123456")





