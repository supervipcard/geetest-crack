import requests
import execjs
import time
import json
from PIL import Image
from io import BytesIO
import base64
import random
import traceback
from retrying import retry
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from image_handle import ImageHandler


class ForbiddenException(Exception):
    pass


class GeetestCrack:
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
        if self.gettype():
            self.get_and_ajax()
        api_get_result = self.api_get()
        if 'bg' in api_get_result and 'fullbg' in api_get_result:
            self.challenge = api_get_result['challenge']  # 滑动验证码获取图片之后challenge的值会改变
            slider_x = self.get_pos(api_get_result['bg'], api_get_result['fullbg'])
            # time.sleep(1)
            try:
                validate = self.api_ajax(slider_x, api_get_result)
            except ForbiddenException:
                return {'code': 2002, 'msg': '验证失败'}
            return {'code': 0, 'result': {'validate': validate, 'challenge': self.challenge}}
        else:
            # pic_type = api_get_result['data']['pic_type']  # 点选验证码类型（文字、图标、空间推理等）
            return {'code': 2001, 'msg': '目前仅支持滑动类型验证码'}

    def gettype(self):
        """判断是否需要点击验证按钮"""
        url = 'https://api.geetest.com/gettype.php?gt={gt}&callback=geetest_{t}'.format(gt=self.gt,
                                                                                        t=int(time.time() * 1000))
        response = self.session.get(url=url)
        type = json.loads(response.text[22: -1])['data']['type']
        return type == 'fullpage'

    def get_and_ajax(self):
        """点击验证按钮"""
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
        """获取图片"""
        url = 'https://api.geetest.com/get.php'
        params = {
            'is_next': 'true',
            'type': '',
            'gt': self.gt,
            'challenge': self.challenge,
            'lang': 'zh-cn',
            'https': 'true',
            'protocol': 'https://',
            'offline': 'false',
            'product': '',
            'api_server': 'api.geetest.com',
            'width': '100%',
            'callback': 'geetest_{}'.format(int(time.time() * 1000)),
        }
        response = self.session.get(url=url, params=params)
        result = json.loads(response.text[22: -1])
        return result

    @retry(stop_max_attempt_number=5, wait_fixed=0)
    def api_ajax(self, x, data):
        """提交验证"""
        with open('slide.js', 'r', encoding='utf-8') as f:
            source = f.read()
        getpass = self.node.compile(source)
        points = self.simulate(x)
        w = getpass.call('outside_link', x, points, data)

        url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w, t=int(time.time() * 1000))
        response = self.session.get(url=url)
        print(response.text)
        result = json.loads(response.text[22: -1])
        if result['message'] == 'forbidden':
            raise ForbiddenException
        return result['validate']

    def get_pos(self, bg, fullbg):
        """获取图片缺口坐标"""
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
        """模拟滑动轨迹"""
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
    url = 'https://passport.bilibili.com/web/captcha/combine?plat=11'.format(int(time.time() * 1000))
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


def tyc_register():
    url = 'https://www.tianyancha.com/verify/geetest.xhtml'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        'Content-Type': 'application/json; charset=UTF-8',
    }
    response = requests.post(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)['data']
    return data['challenge'], data['gt']


def general_register():
    url = 'https://www.geetest.com/demo/gt/register-slide-official?t={}'.format(int(time.time() * 1000))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }
    response = requests.get(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)
    return data['challenge'], data['gt']


def main():
    # challenge, gt, key = register()
    # challenge, gt = tyc_register()
    challenge, gt = general_register()

    try:
        result = GeetestCrack(challenge, gt).start()
    except:
        traceback.print_exc()
        result = {'code': 2003, 'msg': '极验破解服务异常'}
    print(result)

    # if result['code'] == 0:
    #     bilibili(result['result']['challenge'], result['result']['validate'], key)


if __name__ == '__main__':
    main()
