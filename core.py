import os
import time
import re
from pathlib import Path
import json

import requests
from readability import Document

# 初始化
local_time = time.strftime("%y/%m/%d", time.localtime())
brower = requests.Session()
headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "origin": "https://space.bilibili.com"
        }

local_dir = os.getcwd()  # 默认下载地址
os.makedirs(str(Path(local_dir+'/temp')), exist_ok=True)  # 创建临时文件夹

def down_img(img,save_dir):
    sep = '\n'
    with open(save_dir+'/img/url.txt','w') as f:
        f.write(sep.join(img))
    os.system('aria2c --quiet true -j 10 --dir="'+save_dir+'/img" -i "'+save_dir+'/img/url.txt"')
    return

def save(name,data):
    with open(name,'w',encoding='utf-8') as f:
        json.dump(data,f)

#清洗文件名
def clean_name(strs):
    strs = re.sub(r'/:<>?/\^|', "",strs)
    # 去除不可见字符
    return strs

#读取json中的下载列表
def load_json() -> dict:
    """
    读取配置参数
    """
    if os.path.exists('set.json'):
        with open('set.json','r') as f:
            return_data = json.loads(f.read())
    else:
        data = {}
        data['need_down_list'] = []
        data['fin_down_list'] = []
        with open('set.json','w') as f:
            f.write(json.dumps(data))
        return_data = data
    return return_data

#写入下载列表
def save_json(data:dict) -> None:
    """
    读取配置参数
    """
    with open('set.json','w') as f:
        f.write(json.dumps(data))
    return

# 浏览器请求函数
def get(url: str) -> dict:
    """
    请求数据
    """
    try:
        # cj = {i.split("=")[0]:i.split("=")[1] for i in cookies.split(";")}
        response: dict = brower.get(url=url, headers=headers)
        return response.text
    except:
        print('尝试重新访问')
        time.sleep(1)
        get(url)

#获取网站正文文本
def clean(data:str) -> dict:
    """
    获取网页正文内容
    """
    doc = Document(data)
    html = str(doc.summary())
    #获取页面标题
    title = doc.title()
    #对html进行修正以使img正常加载
    need = '<figure class="img-box" contenteditable="false">'
    html = html.replace(need,'<figure>')
    need = '<figure contenteditable="false" class="img-box">'
    html = html.replace(need,'<figure>')
    html = html.replace('data-src','src')
    html = html.replace('src="//','src="https://')
    #获取txt格式
    txt = doc.summary().replace('</p>','\n')#doc.summary()为提取的网页正文但包含html控制符，这一步是替换换行符
    txt = re.sub(r'</?\w+[^>]*>', '', txt)      #这一步是去掉<****>内的内容
    #创个字典存放数据
    fine = {}
    fine['title'] = title
    fine['html'] = html
    fine['txt'] = txt
    return fine

#bilibili api get
def bili_get(url,cookies='null'):
    cookies = {'SESSDATA':cookies}
    data = brower.get(url,headers=headers,cookies=cookies).json()
    return data

#返回cv基础信息
def bili_cv(cv:int) -> dict:
    url = 'http://api.bilibili.com/x/article/viewinfo?id='+str(cv)#调用接口
    info = bili_get(url)
    info = info['data']
    #建立专用存储格式
    box = {}
    #写入正文
    box['html'] = ''
    box['txt'] = ''
    #创建标识符
    box['type'] = 'cv'
    #写入cv信息
    box['title'] = info['title']
    box['mid'] = info['mid']
    box['cover'] = info['origin_image_urls'][0]
    box['writer'] = info['author_name']
    return box

#获取b站文集信息
def bili_rl(rl):
    data = bili_get('http://api.bilibili.com/x/article/list/web/articles?id='+str(rl))
    data =data['data']
    info = {}
    info['name'] = data['list']['name']
    info['summary'] = data['list']['summary']
    info['cover'] = data['list']['image_url']

    #遍历article列表
    cv_info = []
    for list_info in data['articles']:
        a_info = {}
        a_info['id'] = list_info['id']
        a_info['title'] = list_info['title']
        cv_info.append(a_info)
    info['list'] = cv_info
    return info

#批量按up主获取cv号列表
def bili_up_cv(mid:int) -> dict:
    """
    批量按up主获取cv
    """
    #获取up主专栏数量
    input(mid)
    list_num = get('https://api.bilibili.com/x/space/navnum?mid='+str(mid)).json()
    input(list_num)
    list_num = list_num['data']['article']#转换成int类型
    #运算提取页数
    list_page = 1
    num = 0
    while 1 == 1:
        list_page += 1
        num += 30
        if num >= list_num:
            break
    #遍历页面
    list_all_json = []
    for l_num in range(1,list_page):
        url = 'https://api.bilibili.com/x/space/article?mid='+str(mid)+'&pn='+str(l_num)+'&ps=30&sort=publish_time'
        list_json = bili_get(url)
        list_all_json += list_json['data']['articles']
    #处理json
    list_all_info = []
    for info in list_all_json:
        #创建简略信息字典
        clean_info = {}
        clean_info['id'] = info['id']
        clean_info['title'] = info['title']
        list_all_info.append(clean_info)
    return list_all_info

#获取up主文集列表
def bili_up_rl(mid:int) -> dict:
    list_all_json = get('https://api.bilibili.com/x/article/up/lists?mid='+str(mid)+'&sort=0').json()
    list_all_info = []
    for info in list_all_json['data']['lists']:
        #创建简略信息字典
        clean_info = {}
        clean_info['rl'] = info['id']
        clean_info['name'] = info['name']
        clean_info['cover'] = info['image_url']
        clean_info['cv_num'] = info['articles_count']
        list_all_info.append(clean_info)
    return list_all_info

#获取本人收藏夹列表
def get_myfav_list(cookies:str) -> dict:
    #获取收藏夹专栏数量
    list_num = bili_get('https://api.bilibili.com/x/article/favorites/list/all?pn=1&ps=1&jsonp=jsonp',cookies)
    list_num = list_num['data']['page']['total']#转换成int类型
    #运算提取页数
    list_page = 1
    num = 0
    while 1 == 1:
        list_page += 1
        num += 30
        if num >= list_num:
            break
    #遍历页面
    list_all_json = []
    for l_num in range(1,list_page):
        print(l_num)
        url = 'https://api.bilibili.com/x/article/favorites/list/all?pn='+str(l_num)+'&ps=30&jsonp=jsonp'
        list_json = bili_get(url,cookies)
        list_all_json += list_json['data']['favorites']
    #处理json
    list_all_info = []
    for info in list_all_json:
        #跳过失效专栏
        if info['valid'] == False:
            continue
        #创建简略信息字典
        clean_info = {}
        clean_info['id'] = info['id']
        clean_info['title'] = info['title']
        clean_info['words'] = info['words']
        clean_info['stats'] = info['stats']
        list_all_info.append(clean_info)
    return list_all_info

def save_html(data):
    print('数据分析完毕')
    #创建根文件夹
    save_dir = local_dir+'/'+clean_name(data['title'])
    os.makedirs(save_dir,exist_ok=True)
    
    #保存元数据为json以便调用
    print('保存元数据')
    save(save_dir+'/entry.json',data)
    
    print('启动媒体数据本地化')
    #提取图片链接
    old_img_list = re.findall('<img src="(.*?)"',data['html'])
    #创建下载
    os.makedirs(save_dir+'/img',exist_ok=True)#创建临时文件夹
    old_img_list.append(data['cover'])
    cover_name = data['cover'].split('/').pop()
    down_img(old_img_list,save_dir)
    os.rename(save_dir+'/img/'+cover_name,save_dir+'/img/cover.jpg')
    old_img_list.remove(data['cover'])
    print('媒体文件下载完毕')
    # 截取图片文件名
    new_img_list = []
    for url in old_img_list:
        img_name = url.split('/').pop()
        new_img_list.append(img_name)
    #下载cover
    #html本地化
    for num in range(len(new_img_list)):
        data['html'] = data['html'].replace(old_img_list[num],'/img/'+new_img_list[num])
    #创建index.html
    #save_usual(save_dir+'/index.html',data['html'])
    print('索引链接创建完成')
    print('本地化完成')