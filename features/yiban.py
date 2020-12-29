from base import Request
from lxml import etree
import re, time
import websocket
from pyzbar import pyzbar
import json
from PIL import Image
from io import BytesIO
import threading
from multiprocessing.dummy import Pool
poll = Pool()

class BeforeMaterial(Request):
    def get_msg(self):
        ''' 通过websocket获取 '''
        url = 'ws://qrcode.yiban.cn:5000/'
        self.ws = websocket.create_connection(url=url, timeout=15)
        msg = self.ws.recv()  # 接收消息，如果无消息将会堵塞,直到15s超时等待结束
        msg = json.loads(msg)
        poll.apply_async(self.func)
        return msg['msg']

    def func(self):
        self.ws.recv()
        self.ws.close()

    def get_qrcode(self, msg, cookies):
        '''
        获取确认二维码，提取网址
        :param msg: msg
        :return: url
        '''

        url = "http://mp.yiban.cn/confirm/qrcodecreate?code={}&kind=send".format(msg)
        response = self.get(url, cookies=cookies)
        img = Image.open(BytesIO(response.content))
        infos = pyzbar.decode(img)
        infos = [i.data.decode("utf-8") for i in infos]
        return infos[0]

    def confirm(self, qr_url, cookies=None):
        ''' 确认发布 cookies为手机端cookies'''
        access_token = cookies['access_token']
        cookies = {
            "logintoken": access_token,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; OPPO R11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 yiban_android",
            "X-Requested-With": "com.yiban.app",
            "Host": "mp.yiban.cn",
            "appversion": "4.6.13",
            "authorization": access_token,
            "logintoken": access_token,
        }
        response = self.get(qr_url, headers=headers, cookies=cookies)

        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; OPPO R11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 yiban_android",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": qr_url,
            "Origin": "http://mp.yiban.cn",
        }
        confirm_url = "http://mp.yiban.cn/confirm/qrcodeajax"
        cookies.update(dict(response.cookies))
        cookies.update({"client": "android"})

        response = self.post(confirm_url, headers=headers, cookies=cookies, data={"type":1})
        return response

class Material(BeforeMaterial):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
        }

    def build(self, cookies, title, cover="http://img01.fs.yiban.cn/pic/5370552/web/thumb_640x0/3770211755db6f02e26f8c.png",
              showCover="false", summary="", content="", mid=""):
        '''
        保存或者新建素材
        :param cookies: cookies
        :param title: 标题
        :param cover: 封面
        :param showCover: 封面是否放在正文中，bool
        :param summary: 简介
        :param content: 内容，HTML
        :param mid: 修改文章需要此字段，新建不需要
        :return:
        '''
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        url = "http://mp.yiban.cn/material/singlePub"
        data = {
            "title": title,
            "cover": cover,
            "showCover": showCover,
            "summary": summary,
            "content": content,
        }
        if mid:
            data['mid'] = mid

        response = self.post(url, data=data, headers=headers, cookies=cookies)
        return response

    def get_material_ids(self, cookies, page):
        '''
        获取material的id
        :param cookies:
        :param page: 页数，int
        :return: list [('material_id', 'title'), ...]
        '''
        url = "http://mp.yiban.cn/material/index/page/{}".format(page)
        response = self.get(url, cookies=cookies)

        result = re.compile('''<div id="material(\d*?)">[\w\W]*?<div class="msgTxt pull-left">[\w\W]*?<div class="msgTxtTitle">(.*?)</div>''').findall(response.text)
        return result

    def publish(self, material_id, cookies, mobile_cookies=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        msg = self.get_msg()
        qrcode_url = self.get_qrcode(msg, cookies=cookies)
        self.confirm(qrcode_url, cookies=mobile_cookies)

        url = "http://mp.yiban.cn/topic/topicPublish"
        data = {
            'groupids': '',
            'materialid': material_id,
            'rsa': msg,
            'sendToAll': 'true',
            'section': '13827_08ff5cf8e32977689bde4268f73b2e11',
            'isToMobile': 'true',
            'isToProvince': '',
            'isNotice': 'false',
        }
        response = self.post(url, data=data, cookies=cookies, headers=headers)

    def delete(self, material_id):
        ''' 删除素材 '''
        url = "http://mp.yiban.cn/material/materialDel"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        response = self.post(url, data={"materialId":material_id}, headers=headers, cookies=cookies, timeout=10)
        return response



if __name__ == '__main__':
    import sys
    sys.path.append("/home/py/project/egpa3/")
    import private

    from login import YiLogin, UisLoginMobile
    from models.article import ManageIds

    username = private.YIBAN_USERNAME
    password = private.YIBAN_PASSWORD
    cookies = YiLogin(username, password).login()
    super_cookies = UisLoginMobile(ID=private.SUPER_ID).login()

    material = Material()
    manage = ManageIds()

    def test_build():
        response = material.build(cookies, title="易班发文测试", cover="http://img01.fs.yiban.cn/pic/5370552/web/thumb_640x0/3770211755db6f02e26f8c.png",
              showCover="false", summary="", content="test", mid="")
        print(response.text)

    def test_get_material_id():
        result = material.get_material_ids(cookies=cookies, page=1)
        print(result)

    def test_websocket():
        print(material.get_msg())

    def get_qrcode():
        msg = material.get_msg()
        url = material.get_qrcode(msg, cookies=cookies)
        print(url)

    def test_confirm():
        url = "http://mp.yiban.cn/confirm/qrcode?code=ZWRhZjVkOTZjMGU4ZWI3MGJhYTE1ZTJmNTQxM2MwYTQjc2VuZCNhMWM1NmU2MGZjM2NmMGE3OTE3MTUyMjk0ZmFiMDZhMw=="
        material.confirm(qr_url=url, cookies=super_cookies)

    def test_delete():
        id = 1121572
        response = material.delete(id)
        print(response.json())

    def delete_all():
        material_ids = manage.get_all_material()
        print("存储素材数量:{}".format(len(material_ids)))
        index = 0
        print("开始删除--")
        for id in material_ids:
            time.sleep(1)
            index += 1
            response = material.delete(id)
            try:
                result = response.json()
                if result.get('status'):
                    manage.rm_id(id)
                else:
                    print("删除失败(可能已经被删除)")
            except BaseException as e:
                print("出现错误:{}--------------------".format(id))
                print(e)

            if index % 100 == 0:
                print("已完成{}".format(index))

        print("完成删除---")

    delete_all()









