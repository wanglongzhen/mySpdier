# -*- coding:utf-8 -*-

"""
File Name: union.py
Version: 0.1
Description: 基类：包含公共设置

Author: gonghao
Date: 2016/6/23 16:08
"""

from comm_log import comm_log
import requests
import time
import datetime
import calendar
import re
import sys
import ConfigParser
import MySQLdb
import traceback
import os
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


class Union(object):
    """
    公共配置
    """
    def __init__(self, proc_num):
        # 1. 配置日志
        self.logger = comm_log(proc_num)

        # 2. 创建一个Session
        # 2.1 配置头信息
        ua = ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 " +
              "(KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36")
        self.header = {
            "HOST": "iservice.10010.com",
            "Origin": "http://iservice.10010.com",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": r"https://uac.10010.com/portal/homeLogin",
            "Accept": r"application/json, text/javascript, */*; q=0.01",
            "User-Agent": ua,
            "Accept-Encoding": r"deflate",
            "Accept-Language": r"zh-CN,zh;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": r"application/x-www-form-urlencoded;charset=UTF-8"
        }

        #读取日志的路径
        cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
        cfg_path = os.path.join(cur_script_dir, "db.conf")
        cfg_reder = ConfigParser.ConfigParser()
        cfg_reder.readfp(codecs.open(cfg_path, "r", "utf_8"))

        self._SECNAME = "LOGPATH"
        if platform.platform().find("windows") != -1 or platform.platform().find("Windows") != -1:
            self._OPTNAME = "WINDOWS_LOGDIR"
        else:
            self._OPTNAME = "LINUX_LOGDIR"
        self._LOGROOT = cfg_reder.get(self._SECNAME, self._OPTNAME)

        self.imgroot = os.path.join(self._LOGROOT, 'img')
        # 如果目录不存在，则创建一个目录
        if not os.path.isdir(self.imgroot):
            os.makedirs(self.imgroot)

        # 2.2 创建带上述头信息的会话
        self.ses = requests.Session()
        self.ses.headers = self.header

        # 4. 格式化不同不类型的查询信息
        self.keyword_infos = {
            "call": u"通话记录信息",
            "sms": u"短信记录信息",
            "bill": u"历史账单信息",
        }

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
            self.save_db( task_id, phone_num, table, fields, data)
        except Exception, e:
            print traceback.print_exc()
            self.logger.info(u'保存' + table + u'表失败')
            self.logger.info(traceback.format_exc())
            # self.track_back_err_print(sys.exc_info())


    def save_calls(self, task_id, phone_num, data):
        """
        存通话信息
        :param data:
        :return:
        """

        table = 'calls'
        fields = ['call_time', 'receive_phone', 'trade_addr', 'trade_type', 'trade_time', 'call_type']
        try:
            self.save_db( task_id, phone_num, table, fields, data)
        except Exception, e:
            self.logger.info(u'保存' + table + u'表失败')
            self.logger.info(traceback.format_exc())
            # self.track_back_err_print(sys.exc_info())


    def save_sms(self, task_id, phone_num, data):
        """
        存短信信息
        :param data:
        :return:
        """

        table = 'sms'
        fields = ['send_time', 'receive_phone', 'trade_way']
        try:
            self.save_db( task_id, phone_num, table, fields, data)
        except Exception, e:
            self.logger.info(u'保存' + table + u'表失败')
            # self.track_back_err_print(sys.exc_info())
            self.logger.info(traceback.format_exc())


    def save_basic(self, task_id, phone_num, data):
        """
        存基本信息
        :param data:
        :return:
        """

        table = 'basic'
        fields = ['real_name', 'user_source', 'addr', 'id_card', 'phone_remain']
        try:
            self.save_db( task_id, phone_num, table, fields, data)
        except Exception, e:
            self.logger.info(u'保存' + table + u'表失败')
            self.logger.info(traceback.format_exc())
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
            self.logger.error(u"无法写入数据库: " + str(e))
            self.logger.error(sql_ins_format)
        else:
            conn.commit()
            self.logger.info(u'写入数据成功' + table + u', sql : ' + sql_ins_format)
            self.logger.info(u'写入数据成功' + table + u', 写入数据数目： ' + str(len(param)))
        finally:
            cursor.close()
            conn.close()

    def recordErrImg(self):
        """
        记录driver当前的图片
        :return:
        """
        dst_file = os.path.join(self.imgroot, str(self.phone_num) +  '_' + self.get_timestamp() + '.jpg')

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


    def track_back_err_print(self, info):
        """
        格式化输出异常信息
        :param info:
        :return:
        """
        err_info = str(info[0]) + ": " + str(info[1])
        self.logger.info(err_info)
        for file, lineno, function, text in traceback.extract_tb(info[2]):
            self.logger.info(file + "line:" + str(lineno) + "in" + str(function))
            self.logger.info(text)

if __name__ == '__main__':
    union = Union('dd')

