# -*- coding:utf-8 -*-
"""
File Name : 'Spider'.py
Description:
Author: 'wanglongzhen'
Date: '2016/11/20' '21:00'
"""

import sys
import os
import time
import traceback
import datetime
import MySQLdb
import ConfigParser
import calendar
import re
import codecs
import platform

reload(sys)
sys.setdefaultencoding("utf-8")


class GetConn(object):
    """
    获取数据库连接
    """
    def get_db_conn(self, cfg_page = 'db.conf'):
        # 初始化配置文件
        conf = ConfigParser.ConfigParser()
        conf.read(cfg_page)
        print conf.sections()

        host = conf.get('unicom', 'host')
        user = conf.get('unicom', 'username')
        passwd = conf.get('unicom', 'passwd')
        database = conf.get('unicom', 'database')
        port = int(conf.get('unicom', 'port'))

        conn = MySQLdb.connect(host=host, user=user, passwd = passwd, db=database, port = port, charset='utf8')

        return conn

class Operator(object):
    def __init__(self):
        self.init_log()

    def init_log(self, task_id):
        #读取日志的路径
        cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
        cfg_path = os.path.join(cur_script_dir, "db.conf")
        cfg_reder = ConfigParser.ConfigParser()
        cfg_reder.readfp(codecs.open(cfg_path, "r", "utf_8"))

        today = datetime.date.today().strftime('%Y%m%d')

        self._SECNAME = "LOGPATH"
        if platform.platform().find("windows") != -1 or platform.platform().find("Windows") != -1:
            self._OPTNAME = "WINDOWS_LOGDIR"
        else:
            self._OPTNAME = "LINUX_LOGDIR"
        self._LOGROOT = cfg_reder.get(self._SECNAME, self._OPTNAME)

        #创建日志文件的路径
        log_path = os.path.join(self._LOGROOT, today)
        if not os.path.isdir(log_path):
            os.makedirs(log_path)

        self.imgroot = os.path.join(self._LOGROOT, 'img')
        # 如果目录不存在，则创建一个目录
        if not os.path.isdir(self.imgroot):
            os.makedirs(self.imgroot)

    def get_task_no(self, phone_num):
        """
        根据手机号和当前的时间构造一个task_no
        :param user:
        :return:
        """
        task_no = str(phone_num) + "|" + self.get_timestamp()

        return task_no


    def save_bill(self, task_id, phone_num, data):
        """
        存账单信息
        :param data:
        :return:
        """

        table = "bill"
        fields = ['month', 'call_pay']

        try:
            self.save_db(task_id, phone_num, table, fields, data)
        except Exception, e:
            self.write_log(u'保存' + table + u'表失败')
            self.write_log(traceback.format_exc())
            # self.track_back_err_print(sys.exc_info())


    def save_db(self, task_id, phone_num, table, fields, data):
        """
        根据关键词，将结果存入数据库中对应的表中
        :param keyword: 关键词，比如: "basic"
        :param result: [list]，需要存入数据库的内容
        :return:
        """
        if len(data) == 0:
            return

        vs = "'{task_id}', '{mobile}', " + "%s, " * len(fields)
        sql_ins = ("insert into {table} (task_id, mobile, " + ", ".join(fields) +
                   ") values (" + vs[:-2] + ")")
        sql_ins_format = sql_ins.format(table=table,
                                        task_id=task_id,
                                        mobile=phone_num)

        param = [[result_slice[k] for k in fields] for result_slice in data]

        get_conn = GetConn()
        conn = get_conn.get_db_conn()
        cursor = conn.cursor()

        try:
            cursor.executemany(sql_ins_format, param)
        except Exception as e:
            self.write_log(u"无法写入数据库: " + str(e))
            self.write_log(sql_ins_format)
            self.write_log(u'写入数据失败' + table + u', sql : ' + sql_ins_format)
        else:
            conn.commit()
            self.write_log(u'写入数据成功' + table + u', sql : ' + sql_ins_format)
            self.write_log(u'写入数据成功' + table + u', 写入数据数目： ' + str(len(param)))
        finally:
            cursor.close()
            conn.close()


    def write_log(self, message, level = 'INFO'):
        if level == 'INFO':
            self.logger.info(message)
        elif level == 'ERROR':
            self.logger.error(message)
        else:
            self.logger.error(message)

    def recordErrImg(self):
        """
        记录driver当前的图片
        :return:
        """
        dst_file = os.path.join(self.imgroot, str(self.phone_num) + '_' + self.get_timestamp() + '.jpg')

        try:
            if self.driver != None:
                self.driver.save_screenshot(dst_file)
                return True
        except:
            self.logger.info(traceback.format_exc())

        return False


    @staticmethod
    def get_timestamp():
        """
        获取时间戳
        :return: 一个时间戳
        """
        return str(time.time()).replace(".", "0")


    @staticmethod
    def get_begin_end_date(bill_date):
        """
        根据输入的年月，输出当月的起始天数
        :param bill_date: 2015-06
        :return: ["2015-06-01", "2015-06-30"]
        """
        # 检验是否是当月
        today = str(datetime.date.today())
        current_ym = today[:7]
        if current_ym == bill_date:
            return bill_date + "-01", today

        bd = list(map(int, bill_date.split("-")))
        days = calendar.monthrange(*bd)

        return bill_date + "-01", bill_date + "-" + str(days[1])


    @staticmethod
    def convert_c_time(c_time):
        """
        将中文时间转换成秒数：
        "1时1分20秒" => "3680"
        "1分20秒" => "80"
        "20秒" => "20"
        :param c_time: 中文时间
        :return:
        """
        hms = map(int, re.findall(u"\d+", c_time))
        if len(hms) == 3:
            return 3600 * hms[0] + 60 * hms[1] + hms[2]

        if len(hms) == 2:
            return 60 * hms[0] + hms[1]

        if len(hms) == 1:
            return hms[0]

        return None


if __name__ == '__main__':
    operator = Operator()