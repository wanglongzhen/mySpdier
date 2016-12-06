# -*- coding:utf-8 -*-
"""
---------------------------------------------------------------
File Name :  'CommLog'.py
Description:
            线上生产环境通用的Log 模块,日志格式
            日志格式: [时间] [IP] [日志级别] [文件名:行号] 日志信息
            说明：进程号在运行的时候，作为一个运行参数输入

            [
               特别说明：
                   按日期进行回滚的时候 不支持  多进程访问同一个日志文件！！！！！
            ]

Author:  'wangtao'
Date: '2016/6/28' '14:37'
---------------------------------------------------------------
"""
import os
import sys
import logging
import codecs
import ConfigParser
import platform
import time
import logging.config
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler

CommLog_procnum_dict = dict()


class SafeRotatingFileHandler(TimedRotatingFileHandler):
    """
    避免日志覆盖的方案
    """
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding, delay, utc)
        """
        Override doRollover
        lines commanded by "##" is changed by cc
        """
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.

        Override,   1. if dfn not exist then do rename
                 2. _open with "a" model
        """
        if self.stream:
         self.stream.close()
         self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
         timeTuple = time.gmtime(t)
        else:
         timeTuple = time.localtime(t)
         dstThen = timeTuple[-1]
         if dstNow != dstThen:
             if dstNow:
                 addend = 3600
             else:
                 addend = -3600
             timeTuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        ## if os.path.exists(dfn):
        ##     os.remove(dfn)

        # Issue 18940: A file may not have been created if delay is True.
        ##  if os.path.exists(self.baseFilename):
        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.mode = "a"
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)

        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt


# class Singleton(object):
#     def __new__(cls, *args, **kw):
#         if not hasattr(cls, '_instance'):
#             orig = super(Singleton, cls)
#             cls._instance = orig.__new__(cls, *args, **kw)
#         return cls._instance


class CommLog(object):
    def __init__(self, procnum, rotatetype=0, logpath = None):
        """
        指定进程号与回滚类型
        :param procnum: 区分进程号，当多实例时，互不影响
        :param rotatetype: 回滚类型，0 表示按时间回滚，1 表示按大小回滚
        """
        self._procnum = procnum
        self._SECNAME = "LOGPATH"
        self._TIME_SECNAME = "TIME_ROTATE"  # 日志回滚时间配置项
        self._SIZE_SECNAME = "SIZE_ROTATE"  # 按大小进行日志回滚配置项
        self._TIME_ROTATE_TYPE = 0
        self._SIZE_ROTATE_TYPE = 1

        # 分不同的操作系统
        if platform.platform().find("windows") != -1 or platform.platform().find("Windows") != -1:
            self._OPTNAME = "WINDOWS_LOGDIR"
        else:
            self._OPTNAME = "LINUX_LOGDIR"

        # self._LOGFORMAT = logging.Formatter("[%(asctime)s] [%(process)s] [%(levelname)-7s] [%(filename)s :%(lineno)d] [%(module)s] %(message)s")
        self._LOGFORMAT = logging.Formatter('[%(name)-12s]: [%(levelname)-6s] [%(asctime)s]: %(message)s')

        # 解析配置文件，获取日志路径，日志回滚配置
        cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
        cfg_path = os.path.join(cur_script_dir, "db.conf")
        cfg_reder = ConfigParser.ConfigParser()
        cfg_reder.readfp(codecs.open(cfg_path, "r", "utf_8"))
        # 日志路径配置
        if logpath != None:
            self._LOGROOT = logpath
        else:
            self._LOGROOT = cfg_reder.get(self._SECNAME, self._OPTNAME)
        # 日志回滚配置
        self._LOGWHEN = cfg_reder.get(self._TIME_SECNAME, "WHEN")
        self._LOGINTVAL = int(cfg_reder.get(self._TIME_SECNAME, "INTVAL"))
        self._LOGMAXBACKUP_TIME = int(cfg_reder.get(self._TIME_SECNAME, "MAX_BACKUP"))

        self._LOGMAXSIZE = int(cfg_reder.get(self._SIZE_SECNAME, "MAXSIZE"))
        self._LOGMAXBACKUP_SIZE = int(cfg_reder.get(self._SIZE_SECNAME, "MAX_BACKUP"))

        # 如果目录不存在，则创建一个目录
        if not os.path.isdir(self._LOGROOT):
            os.makedirs(self._LOGROOT)

        # 定义两个日志handler,多实例进程的时候，为每个进程指定一个日志文件编号
        self._debug_lname = os.path.join(self._LOGROOT, "sys-{0}.log".format(procnum))
        self._error_lname = os.path.join(self._LOGROOT, "sys-err-{0}.log".format(procnum))
        self._critical_lname = os.path.join(self._LOGROOT, "sys-critical-{0}.log".format(procnum))

        # 初始化两个 logger
        # 设置 root logger 的level 是debug的
        logging.getLogger().setLevel("DEBUG")
        self.init_debug_logger(rotatetype)
        self.init_error_debug(rotatetype)
        self.init_critical_logger(rotatetype)

    def init_debug_logger(self, rotatetype):
        """
        初始化 debug,info 级别的日志 logger
        """
        self._LOGGER_DEBUG = logging.getLogger(str(self._procnum) + "-DEBUG")
        self.Rthandler_Debug = None
        if rotatetype == self._TIME_ROTATE_TYPE:
            self.Rthandler_Debug = TimedRotatingFileHandler(self._debug_lname,
                                                            when=self._LOGWHEN,
                                                            interval=self._LOGINTVAL,
                                                            backupCount=self._LOGMAXBACKUP_TIME)
        else:
            self.Rthandler_Debug = RotatingFileHandler(self._debug_lname,
                                                       maxBytes=self._LOGMAXSIZE,
                                                       backupCount=self._LOGMAXBACKUP_SIZE)

        self.Rthandler_Debug.setLevel(logging.DEBUG)
        self.Rthandler_Debug.setFormatter(self._LOGFORMAT)
        self._LOGGER_DEBUG.addHandler(self.Rthandler_Debug)

    def init_error_debug(self, rotatetype):
        """
        初始化 error 级别的日志logger
        :return:
        """
        self._LOGGER_ERROR = logging.getLogger(str(self._procnum) + "-ERROR")
        self.Rthandler_Error = None
        if rotatetype == self._TIME_ROTATE_TYPE:
            self.Rthandler_Error = TimedRotatingFileHandler(self._error_lname,
                                                            when=self._LOGWHEN,
                                                            interval=self._LOGINTVAL,
                                                            backupCount=self._LOGMAXBACKUP_TIME)
        else:
            self.Rthandler_Error = RotatingFileHandler(self._error_lname,
                                                       maxBytes=self._LOGMAXSIZE,
                                                       backupCount=self._LOGMAXBACKUP_SIZE)
        self.Rthandler_Error.setLevel(logging.ERROR)
        self.Rthandler_Error.setFormatter(self._LOGFORMAT)
        self._LOGGER_ERROR.addHandler(self.Rthandler_Error)

    def init_critical_logger(self, rotatetype):
        self._LOGGER_CRITICAL = logging.getLogger(str(self._procnum) + "-CRITICAL")
        if rotatetype == self._TIME_ROTATE_TYPE:
            self.Rthandler_CRITICAL = TimedRotatingFileHandler(self._critical_lname,
                                                               when=self._LOGWHEN,
                                                               interval=self._LOGINTVAL,
                                                               backupCount=self._LOGMAXBACKUP_TIME)
        else:
            self.Rthandler_CRITICAL = RotatingFileHandler(self._critical_lname,
                                                          maxBytes=self._LOGMAXSIZE,
                                                          backupCount=self._LOGMAXBACKUP_SIZE)
        self.Rthandler_CRITICAL.setLevel(logging.CRITICAL)
        self.Rthandler_CRITICAL.setFormatter(self._LOGFORMAT)
        self._LOGGER_CRITICAL.addHandler(self.Rthandler_CRITICAL)

    def debug(self, logmsg):
        """
        打印debug级别的日志
        :param logmsg:
        :return:
        """
        strmsg = "[{pnum}] {msg}".format(pnum=self._procnum, msg=logmsg)
        self._LOGGER_DEBUG.debug(strmsg)

    def info(self, logmsg):
        """
        打印 info 级别的日志接口
        :param logmsg:
        :return:
        """
        strmsg = "[{pnum}] {msg}".format(pnum=self._procnum, msg=logmsg)
        self._LOGGER_DEBUG.info(strmsg)

    def error(self, logmsg):
        """
        打印 error 级别的日志接口
        :param logmsg:
        :return:
        """
        strmsg = "[{pnum}] {msg}".format(pnum=self._procnum, msg=logmsg)
        self._LOGGER_ERROR.error(strmsg)

    def warning(self, logmsg):
        """
        打印 warn 级别的日志接口
        :param logmsg:
        :return:
        """
        strmsg = "[{pnum}] {msg}".format(pnum=self._procnum, msg=logmsg)
        self._LOGGER_DEBUG.warning(strmsg)

    def critical(self, logmsg):
        """
        打印 critical 级别的日志接口
        :param logmsg:
        :return:
        """
        strmsg = "[{pnum}] {msg}".format(pnum=self._procnum, msg=logmsg)
        self._LOGGER_CRITICAL.critical(strmsg)


def comm_log(procnum, logpath=None):
    if procnum not in CommLog_procnum_dict:
        logger = CommLog(procnum, logpath=logpath)
        CommLog_procnum_dict[procnum] = logger

    return CommLog_procnum_dict[procnum]


if __name__ == "__main__":
    # import time
    if len(sys.argv) == 1:
        procnum = 0
    else:
        procnum = int(sys.argv[1])

    loginst = CommLog(procnum)

    # 测试代码
    """
    for i in range(100):
        loginst.debug("This is debug infomation")
        loginst.info("This is info infomation")
        loginst.error("This is error infomation")
        time.sleep(10)
    """
