import re
import os
import time
import threading #多进程库
from pathlib import Path #路径库
import platform#获取系统信息

import requests
import pywebio as io
out = io.output
ioin = io.input
pin = io.pin

import core #导入python核心接口
now_path = os.path.dirname(os.path.realpath(__file__))+"/"

#声明下载列表
set_info = core.load_json()
#获取当前平台
system_type = platform.system()#系统名称
system_bit = platform.machine()#操作系统位数
#启动时间
local_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
downloading_list=[]
downloaded_list=[]
download_line=0


#解析输入的链接类型
def get_url_type(url:str) -> list:
    if '/read/' in url:
        if '/cv' in url:#匹配cv
            return_data = re.search('/cv([0-9]*)',url).group()
            return ['cv',return_data]
        elif '/readlist/' in url:#匹配rl
            return_data = re.search('/rl([0-9]*)',url).group()
            return ['rl',return_data]
        return
    elif 'space.bilibili.com' in url:#up主类
        return_data = re.search('space.bilibili.com/([0-9]*)',url).group()
        return ['up',return_data]

#校验输入是否正确
def check_input_url(url:str):
    if '/read/' in url:#cv rl类
        return
    elif 'space.bilibili.com' in url:#up主类
        return
    return '输入链接错误'

#获取信息
def get_info(url_type:str,id:str) -> dict:
    if url_type == 'cv':
        return_data = core.bili_cv(id)
        return return_data
    elif url_type == 'rl':
        return_data = core.bili_rl(id)
        return return_data
    elif url_type == 'up':
        return_data = core.bili_up_cv(id)
        return return_data

#显示信息
def print_info(info):
    """
    创建专栏信息显示页
    """

#解析输入的url
def start_url():
    global download_line
    url = pin.pin['url_input']#获取输入
    check_return = check_input_url(url)
    if check_return != None:
        out.toast(check_return,duration=3,color='error')#显示错误信息
        return
    #解析url
    out.toast("开始解析下载...",duration=3,color='loading')
    out_url = get_url_type(url)
    temp_title=get_title(str(out_url[1]))
    download_line+=1
    downloading_list.append(temp_title)
    update()
    info = get_info(out_url[0],str(out_url[1]))
    save_file=core.save(info)
    del downloading_list[0]
    downloaded_list.append(temp_title)
    update()
    out.toast("解析下载已完成，请检查"+save_file+"是否存在专栏目录",duration=3,color='success')

def get_title(id):
    temp_url='http://api.bilibili.com/x/article/viewinfo?id='+str(id)[3:len(str(id))]
    temp_info=core.api_get(temp_url)
    temp_title=temp_info["data"]["title"]
    return temp_title

def update():
    with out.use_scope('main'):
        with out.use_scope('down'):
            scope_down_work = out.put_table([downloading_list])
            scope_down_fin = out.put_table([downloaded_list])
            out.clear('down')
            out.put_tabs([{'title':'下载中','content':scope_down_work},{'title':'下载完成','content':scope_down_fin}])#创建横向标签栏

if __name__ == "__main__":
    with out.use_scope('main'):#创建并进入main域
        out.scroll_to('main','top')
        #创建横向标签栏
        scope_url = out.put_scope('url')#创建url域
        scope_set = out.put_scope('set')#创建set域
        scope_down = out.put_scope('down')#创建down域
        out.put_tabs([{'title':'链接解析','content':scope_url},{'title':'下载列表','content':scope_down},{'title':'设置','content':scope_set}])#创建

        #创建url输入框
        with out.use_scope('url'):#进入域
            pin.put_input('url_input',label='请输入链接',type='text')#限制类型为url,使用check_input_url检查内容
            out.put_button(label='解析链接',onclick=start_url).style('width: 100%')#创建按键
            out.put_scope('video_info')
            
        #创建下载列表
        with out.use_scope('down'):
            #scope_down_work = out.put_scope('down_work')
            #scope_down_fin = out.put_scope('down_fin')
            scope_down_work = out.put_table([downloading_list])
            scope_down_fin = out.put_table([downloaded_list])
            out.put_tabs([{'title':'下载中','content':scope_down_work},{'title':'下载完成','content':scope_down_fin}])#创建横向标签栏
