# -*- coding:utf-8 -*-

"""
File Name: generate_report.py
Version: 0.1
Description: 生成报告

Author: gonghao
Date: 2016/10/26 11:13
"""
import datetime
import traceback
import time
import json
import sys


from dateutil.relativedelta import relativedelta
from mongodb_connect import connect_mongodb
from models import Basic, Bill, Sms, Call, PackageUsage, Recharge, TaskReport
import comm_log

reload(sys)
sys.setdefaultencoding("utf-8")


class CMCCReport(object):
    def __init__(self, proc_num, task_id, phone):

        self.task_id = task_id
        self.phone = phone
        self.proc_num = proc_num

        self.conn = connect_mongodb()

        # 日志
        self.logger = comm_log.comm_log(self.proc_num, "")

    def __enter__(self):
        self.logger.info(u"-------------------------------------------------")
        self.logger.info(u"开始生成报告：" + str(self.task_id) + '-' + str(self.phone))
        self.logger.info(u"-------------------------------------------------")

        self.start_time = time.time()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.critical(str(self.task_id) + ' - ' + str(self.phone))
            self.logger.critical(exc_type)
            self.logger.critical(exc_val)
            self.logger.critical(''.join(traceback.format_tb(exc_tb)))

        if self.conn is not None:
            self.conn.close()

        self.logger.info(u"-------------------------------------------------")
        self.logger.info(u"解析文件完毕：" + str(self.task_id) + '-' + str(self.phone))
        self.logger.info(u"-------------------------------------------------")

        self.end_time = time.time()
        print self.end_time - self.start_time

    def generate_basic(self, search_dt):
        """
        获取指定日期的个人信息
        :param search_dt:
        :return:
        """
        basic = json.loads(Basic.objects(task_id=self.task_id, scrape_dt=str(search_dt)).first().to_json())
        del basic["_id"]
        del basic["task_id"]
        del basic["scrape_dt"]

        return basic

    def generate_pu(self, search_dt):
        """
        根据指定日期获取当月的套餐余量
        :param search_dt:
        :return:
        """
        pu = json.loads(PackageUsage.objects(task_id=self.task_id, bill_end_date=str(search_dt)).first().to_json())
        del pu["_id"]
        del pu["task_id"]
        del pu["mobile"]

        return pu

    def generate_bill(self, bill_start_month):
        """
        根据给定的日期, 获取指定的账单记录
        :param bill_start_month:
        :return:
        """
        bill = json.loads(Bill.objects(mobile=self.phone, bill_month__gte=bill_start_month).to_json())
        for item in bill:
            del item["_id"]
            del item["task_id"]
            del item["mobile"]

        return bill

    def generate_call(self, bill_start_day):
        """
        根据指定的日期, 获取指定的通话记录
        :param bill_start_day:
        :return:
        """
        call = json.loads(Call.objects(mobile=self.phone, time__gte=bill_start_day).to_json())
        for item in call:
            del item["_id"]
            del item["task_id"]
            del item["mobile"]

        return call

    def generate_sms(self, bill_start_day):
        """
        根据指定的日期, 获取指定的短信记录
        :param bill_start_day:
        :return:
        """
        sms = json.loads(Sms.objects(mobile=self.phone, time__gte=bill_start_day).to_json())
        for item in sms:
            del item["_id"]
            del item["task_id"]
            del item["mobile"]

        return sms

    def generate_recharge(self, bill_start_day):
        """
        根据指定的日期, 获取指定的充值记录
        :param bill_start_day:
        :return:
        """
        recharge = json.loads(Recharge.objects(mobile=self.phone, recharge_time__gte=bill_start_day).to_json())
        for item in recharge:
            del item["_id"]
            del item["task_id"]
            del item["mobile"]

        return recharge

    def generate_flow(self):
        """
        生成报告流程
        :return:
        """
        # 1. 计算账单日期
        today = datetime.date.today()
        bill_start_month = str(today + relativedelta(months=-6))[:7]
        bill_start_day = bill_start_month + "-01 00:00:00"

        # 2. 生成报告
        infos = dict()
        infos["task_id"] = self.task_id
        infos["generate_dt"] = str(datetime.datetime.now())[:19]

        # 2.1 个人信息与套餐余量
        infos["basic"] = self.generate_basic(today)
        infos["package_usage"] = self.generate_pu(today)

        # 2.2 历史账单、电话、短信以及充值记录
        infos["bill"] = self.generate_bill(bill_start_month)
        infos["call"] = self.generate_call(bill_start_day)
        infos["sms"] = self.generate_sms(bill_start_day)
        infos["recharge"] = self.generate_recharge(bill_start_day)

        # 3. 组合成一份报告
        task_report = TaskReport()

        task_report["task_id"] = self.task_id
        task_report["mobile"] = self.phone
        task_report["report"] = json.dumps(infos)
        task_report["scrape_dt"] = str(datetime.datetime.now())

        task_report.save()


def generate_report(proc_num, task_id, phone):
    """
    移动爬取生成报告
    :param proc_num: 进程编码
    :param task_id: 任务ID
    :param phone: 手机号
    :return:
    """
    with CMCCReport(proc_num, task_id, phone) as cr:
        cr.generate_flow()

if __name__ == "__main__":
    generate_report("201", "cmcc_web_1478482589753", "18794224550")
