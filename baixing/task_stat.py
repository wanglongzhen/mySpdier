#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'task_stat'.py 
Description:
Author: 'zhengyang' 
Date: '2016/8/1' '12:27'
"""
import datetime
from collections import OrderedDict
import pymssql
import sendmail
import sys


class Dao(object):

    def __init__(self, host, user, password, database):
        """mssql's host, user, password, db, port"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def select_danbaobaoxian(self, cal_date):
        """baixing项目"""

        try:
            conn = pymssql.connect(host=self.host, user=self.user,
                                   password=self.password, database=self.database, charset='utf8')
            cur = conn.cursor()
            cur.execute("""select count(1)
                           from tagphone.dbo.danbaobaoxian
                           where source = 3
                           and add_time > (%s)
                           """, cal_date)
            values = cur.fetchall()
            return values[0][0]
        except Exception, e:
            print "pymssql Error", e
        finally:
            cur.close()
            conn.close()

    def select_collection_post(self, cal_date):
        """58项目"""
        try:
            conn = pymssql.connect(host=self.host, user=self.user,
                                   password=self.password, database=self.database, charset='utf8')
            cur = conn.cursor()
            cur.execute("""select count(1)
                           from tagphone.dbo.phonemark_58
                           where create_time > (%s)
                           """, cal_date)
            values = cur.fetchall()
            return values[0][0]
        except Exception, e:
            print "pymssql Error", e
        finally:
            cur.close()
            conn.close()

dao = Dao("99.48.58.208", "sa", "mime@123", "BlacklistAll")


class TaskStat(object):
    def __init__(self):
        self.cal_date = datetime.date.today()
        self.cal_date_6 = self.cal_date - datetime.timedelta(days=6)
        self.task_count = OrderedDict()

    def run(self):
        self.task_count[u"百姓"] = dao.select_danbaobaoxian(self.cal_date_6)
        self.task_count[u"58"] = dao.select_collection_post(self.cal_date_6)
        self.task_count[u"总计"] = sum(self.task_count.values())

    def get_text(self):
        to = ['longzhen.wang@mi-me.com', 'tao.wang@mi-me.com']
        subject = u"百姓、58爬取数量{0}-{1}".\
            format(datetime.datetime.strftime(self.cal_date_6, '%Y/%m/%d'),
                   datetime.datetime.strftime(self.cal_date, '%Y/%m/%d'))
        text_list = []
        for k, v in self.task_count.items():
            text_str = u"{0}: {1}".format(k, v)
            text_list.append(text_str)
        text = "\n".join(text_list)
        return to, subject, text

if __name__ == "__main__":

    task_stat = TaskStat()
    task_stat.run()
    to, subject, text = task_stat.get_text()
    sendmail.intf_send_mail(to, subject, text)
    print text
    # if len(sys.argv) == 2:
    #     # 参数为1时发送邮件
    #     if sys.argv[1] == '1':
    #         print "start to send mail"
    #         sendmail.intf_send_mail(to, subject, text)
    #         print "has send mail"
