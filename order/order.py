from flask import Flask
from flask import request

import json
import sys

import multiprocessing

reload(sys)
sys.setdefaultencoding("utf-8")



app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/ic/list', methods=['POST', 'GET'])
def ic_list():
    return getBaseReturnValue(data=[], msg="Error", code=False)

@app.route('/login', methods=['POST'])
def login():

    user = request.args.get('user')

    ret_data = dict()
    ret_data['error_no'] = 0
    ret_data['task_no'] = '13233134|13143134'
    ret_data['message'] = ''

    lock.acquire()
    _q.put("dd")
    lock.release()

    return getBaseReturnValue(data=ret_data, msg="Error", code=False, task_no= '13233134|13143134')


@app.route('/login_sms', methods=['POST'])
def login_sms():
    user = request.args.get('user')

    ret_data = dict()
    ret_data['error_no'] = 0
    ret_data['task_no'] = '13233134|13143134'
    ret_data['message'] = ''

    lock.acquire()
    value = _q.get()
    lock.release()


    return getBaseReturnValue(data=ret_data, msg="Error", code=False, task_no= '13233134|13143134')


def getBaseReturnValue(data,msg,code, task_no):
    json_data = json.dumps({'datas':data,'msg':msg,'success':code, 'task_no':task_no},ensure_ascii=False,encoding='gb2312')
    return json_data

if __name__ == '__main__':
    _manager = multiprocessing.Manager()
    _q = _manager.Queue()
    lock = _manager.Lock()

    app.run()
