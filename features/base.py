import requests

class Request():
    def request(self, method, url, *, headers=None, cookies=None, **kwargs):
        '''
        # 请求
        '''
        # 设置headers
        if not headers:
            if hasattr(self, 'headers'):
                headers = self.headers
            else:
                headers = {}
        # 设置cookies
        if not cookies:
            if hasattr(self, 'cookies'):
                cookies = self.cookies
            else:
                cookies = {}

        return requests.request(method, url, headers=headers, cookies=cookies, **kwargs)

    def get(self, url, *, headers=None, cookies=None, **kwargs):
        ''' 一个get请求 '''
        return self.request("GET", url, headers=headers, cookies=cookies, **kwargs)

    def post(self, url, *, headers=None, cookies=None, **kwargs):
        ''' 一个post请求 '''
        return self.request("POST", url, headers=headers, cookies=cookies, **kwargs)