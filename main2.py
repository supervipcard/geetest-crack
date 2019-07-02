import requests
import execjs
import time
import json
from PIL import Image
from io import BytesIO
import base64
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from image_handle import ImageHandler


class Geetest:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }

    def __init__(self, challenge, gt):
        self.challenge = challenge
        self.gt = gt
        self.session = requests.Session()
        self.session.headers = self.headers
        self.node = execjs.get('Node')

    def start(self):
        self.get_and_ajax()  # 点击验证按钮
        api_get_result = self.api_get()  # 获取图片
        self.challenge = api_get_result['challenge']
        self.gt = api_get_result['gt']
        slider_x = self.get_pos(api_get_result['bg'], api_get_result['fullbg'])  # 获取图片缺口坐标
        time.sleep(1)
        return self.api_ajax(slider_x, self.simulate(slider_x), api_get_result)  # 验证

    def get_and_ajax(self):
        with open('fullpage.js', 'r', encoding='utf-8') as f:
            source = f.read()
        getpass = self.node.compile(source)
        E, w_get = getpass.call('outside_link', self.challenge, self.gt)

        get_url = 'https://api.geetest.com/get.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w_get, t=int(time.time() * 1000))
        get_response = self.session.get(url=get_url)
        data = json.loads(get_response.text[22: -1])['data']

        with open('fullpage2.js', 'r', encoding='utf-8') as f:
            source = f.read()
        getpass = self.node.compile(source)
        w_ajax = getpass.call('outside_link', self.challenge, self.gt, E, data)

        ajax_url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w_ajax, t=int(time.time() * 1000))
        self.session.get(url=ajax_url)

    def api_get(self):
        url = 'https://api.geetest.com/get.php'
        params = {
            'is_next': 'true',
            'type': 'slide3',
            'gt': self.gt,
            'challenge': self.challenge,
            'lang': 'zh-cn',
            'https': 'true',
            'protocol': 'https://',
            'offline': 'false',
            'product': 'embed',
            'api_server': 'api.geetest.com',
            'width': '100%',
            'callback': 'geetest_{}'.format(int(time.time() * 1000)),
        }
        response = self.session.get(url=url, params=params)
        data = json.loads(response.text[22: -1])
        return data

    def api_ajax(self, x, points, data):
        with open('slide.js', 'r', encoding='utf-8') as f:
            source = f.read()
        getpass = self.node.compile(source)
        w = getpass.call('outside_link', x, points, data)

        url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w, t=int(time.time() * 1000))
        response = self.session.get(url=url)
        print(response.text)
        result = json.loads(response.text[22: -1])
        return result.get('validate')

    def get_pos(self, bg, fullbg):
        bg_url = 'https://static.geetest.com/' + bg
        bg_response = self.session.get(url=bg_url)
        bg_image = Image.open(BytesIO(bg_response.content))

        fullbg_url = 'https://static.geetest.com/' + fullbg
        fullbg_response = self.session.get(url=fullbg_url)
        fullbg_image = Image.open(BytesIO(fullbg_response.content))

        pos = ImageHandler.subtract(bg_image, fullbg_image)
        return pos

    @staticmethod
    def simulate(pos):
        points = list()
        points.append([0, 0, 0])
        x = 0
        t = random.randint(50, 80)
        while abs(x - pos) > 10:
            x += random.randint(1, 5)
            t += random.randint(15, 30)
            points.append([int(x), 0, int(t)])

        while abs(x - pos) <= 10:
            x += random.randint(0, 1)
            t += random.randint(15, 30)
            points.append([int(x), 0, int(t)])
            if x == pos:
                break

        t += random.randint(200, 300)
        points.append([int(x), 0, int(t)])
        return points


def register():
    url = 'https://passport.bilibili.com/web/captcha/combine?plat=11'.format(int(time.time()*1000))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }
    response = requests.get(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)['data']['result']
    return data['challenge'], data['gt'], data['key']


def bilibili(challenge, validate, key):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'passport.bilibili.com',
        'Origin': 'https://passport.bilibili.com',
        'Referer': 'https://passport.bilibili.com/login',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
    }

    url = 'https://passport.bilibili.com/login?act=getkey'
    response = requests.get(url=url, headers=headers)
    print(response.text)
    result = json.loads(response.text)

    message = result['hash'] + 'pl1996317'
    public_key = result['key']
    public_key = RSA.importKey(public_key)  # 导入读取到的公钥
    rsa = PKCS1_v1_5.new(public_key)  # 生成对象
    password = base64.b64encode(rsa.encrypt(message.encode("utf-8"))).decode('utf8')
    print(password)

    url = 'https://passport.bilibili.com/web/login/v2'
    data = {
        'captchaType': '11',
        'username': '15058716965',
        'password': password,
        'keep': 'true',
        'key': key,
        'goUrl': 'https://www.bilibili.com/',
        'challenge': challenge,
        'validate': validate,
        'seccode': '{}|jordan'.format(validate)
    }
    response = requests.post(url=url, headers=headers, data=data)
    print(response.text)


def main():
    challenge, gt, key = register()
    geetest = Geetest(challenge, gt)
    validate = geetest.start()
    if validate:
        pass
        # bilibili(geetest.challenge, validate, key)
    else:
        print('失败')


if __name__ == '__main__':
    main()
