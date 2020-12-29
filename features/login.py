from lxml import etree
import base64
from utils import rsa
from utils.chaojiying import Chaojiying_Client
import private
from base import Request
import re

chaojiying = Chaojiying_Client(private.CODE_USERNAME, private.CODE_PASSWORD, private.CODE_NUMBER)


class YiLogin(Request):
    '''
    直接通过模拟易班登录方式进行登录
    '''
    def __init__(self, username, password):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
        }
        self.headers2 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        self.username = username
        self.password = password

    def login(self):
        cookies, public_key = self.access()
        # 进行加密
        password = self._encrypt(self.password, public_key)

        status = self.submit(self.username, password, headers=self.headers2, cookies=cookies, captcha='')
        if status['status']:
            return cookies
        elif status['data']['captcha']:
            captcha = self.get_graph(cookies=cookies, headers=self.headers2)
            status = self.submit(self.username, password, headers=self.headers2, cookies=cookies, captcha=captcha)
            if status['status']:
                return cookies
        else:
            raise Exception("1、检查账号密码 2、检查网络情况 3、检查打码平台是否欠费 4、检查易班的登陆页面")

    def access(self, headers=None):
        '''
        最开始的访问
        :return: 一个元组，(cookies, 公钥)
        '''
        url = "https://mp.yiban.cn/login/index"
        response = self.get(url, headers=headers)

        tree = etree.HTML(response.text)
        public_key = tree.xpath("//input[@id='pubkey']/@value")[0]
        return response.cookies, public_key

    def submit(self, username, password, headers=None, cookies=None, captcha=""):
        '''
        提交账号密码盒验证码
        :return:提交账号密码之后的登陆状态
        '''
        url = "https://mp.yiban.cn/login/loginAjax"
        data = {
            "account": username,
            "password": password,
            "captcha": captcha,
        }
        response = self.post(url, headers=headers, data=data, cookies=cookies)
        return response.json()

    def get_graph(self, headers=None, cookies=None):
        '''
        获取验证码
        :return: 二进制图片数据
        '''
        url = "https://mp.yiban.cn/login/getGraphCode"
        response = self.post(url, headers=headers, cookies=cookies)
        result = response.json()['data']['data']['img']
        result = result.split(",")[1]
        content = base64.b64decode(result)

        code = self._identify_code(content)
        return code

    def _identify_code(self, content):
        '''
        通过打码平台验证识别验证码
        :param content:图片文件流
        :return: 字符串
        '''
        result = chaojiying.PostPic(content, 2001)
        return result['pic_str']

    def _encrypt(self, password, public_key):
        '''
        对密码进行加密
        :return: 加密之后的密码
        '''
        return rsa.encrypt(password, public_key)


class UisLogin(Request):
    '''
    通过Uis认证进行登录
    '''
    def __init__(self, ID):
        '''
        :param ID: 数据库对应的id或者学号
        '''
        self.ID = ID

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
        }

    def login(self):
        url = "https://o.yiban.cn/uiss/check?scid=10002_0"
        data = self.get_data(self.ID)
        response = self.post(url, data=data)  # 获取access_token
        return response.cookies

    def get_data(self,ID):
        ''' uis登录接口 '''
        url = private.UIS_URL + "?ID=" + str(ID)
        response = self.get(url)

        tree = etree.HTML(response.text)
        data = {
            "say": tree.xpath("//input//@value")[0],
        }
        return data


class UisLoginMobile(UisLogin):
    ''' 通过uis认证登录易班手机版app '''
    def __init__(self, ID):
        self.ID = ID
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; OPPO R11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36",
        }

    # 这步被确认非必要，仅暂时保留，当前没有使用此接口
    def get_laravel_session(self):
        ''' 在手机端会有一个session保持不变，需要获取, 暂时不确定这个必须，有待确定 '''
        url = "http://mobile.yiban.cn/api/passport/schooluislist"
        response = self.get(url)

    def login(self):
        url = "https://o.yiban.cn/uiss/check?scid=10002_0&type=mobile" # &goto=http://proj.yiban.cn/project/invest/test.php
        data = self.get_data(self.ID)
        response = self.post(url, data=data)
        return self.verify_login(response.cookies)

    def verify_login(self, cookies):
        ''' 验证是否登录成功，并返回完整的cookies '''
        cookies = dict(cookies)
        response = self.get("http://mobile.yiban.cn/api/passport/loginsucess", cookies=cookies)
        if re.compile("(登陆成功)").findall(response.text):
            cookies.update(dict(response.cookies))
            cookies.update({"visit_school":"10002"})
            return cookies
        else:
            return None


if __name__ == '__main__':
    ID = private.SUPER_ID
    username = private.YIBAN_USERNAME
    password = private.YIBAN_PASSWORD

    def test_login_yiban():
        login = YiLogin(username, password)
        print(login.login())

    def test_login_uis():
        super_cookies = UisLogin(ID=ID).login()
        print(super_cookies)

    def test_login_uis_mobile():
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; OPPO R11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36",
        }
        import requests
        super_cookies = UisLoginMobile(ID=ID).login()
        print(super_cookies)

    test_login_uis_mobile()
