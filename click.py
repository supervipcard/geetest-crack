import itertools
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
import matplotlib.pyplot as plt

from yolo import YOLO

lis = list()


def on_press(event):
    lis.append((event.button, int(event.xdata), int(event.ydata)))


class ForbiddenException(Exception):
    pass


def get_proxies():
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"

    proxyUser = "H889BT3GSSBG3U6D"
    proxyPass = "C4E4EA69296C97B8"

    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxyHost,
        "port": proxyPort,
        "user": proxyUser,
        "pass": proxyPass,
    }

    proxies = {
        "http": proxyMeta,
        "https": proxyMeta,
    }
    return proxies


proxies = get_proxies()


class GeetestCrack:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }

    def __init__(self, challenge, gt):
        self.challenge = challenge
        self.gt = gt
        self.session = requests.Session()
        # self.session.proxies = proxies
        self.session.headers = self.headers
        self.node = execjs.get('Node')
        self.yolo = YOLO()

    def start(self):
        # if self.challenge and self.gettype():
        self.get_and_ajax()
        api_get_result = self.api_get()
        pic_type = api_get_result['data']['pic_type']
        if pic_type == 'word':
            coord = self.get_coord(api_get_result['data']['pic'])

            for points in itertools.permutations(coord, len(coord)):
                print(points)
                coord = ','.join([str(i[0]) + '_' + str(i[1]) for i in points])
                self.api_ajax_click(coord, api_get_result['data'])
        else:
            return {'code': 1004, 'message': '目前暂不支持{}类型验证码'.format(pic_type)}

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

    def get_coord(self, bg):
        """获取图片缺口坐标"""
        bg_url = 'https://static.geetest.com/' + bg
        bg_response = self.session.get(url=bg_url)
        bg_image = Image.open(BytesIO(bg_response.content))
        bg_image = bg_image.crop((0, 0, 344, 344))
        bg_image.save('a.jpg')

        out_boxes = self.yolo.detect_image(bg_image)
        out_boxes = out_boxes.tolist()

        lis = list()
        for box in out_boxes:
            x = int((box[1] + box[3]) / 2)
            y = int((box[0] + box[2]) / 2)
            lis.append((x, y))
        print(lis)

        value = [[int(i[0]/344*10000), int(i[1]/344*10000)] for i in lis]
        print(value)

        # coord = ','.join([str(i[0]) + '_' + str(i[1]) for i in value])
        return value

    def api_ajax_click(self, points, data):
        """提交验证"""
        with open('click.js', 'r', encoding='utf-8') as f:
            source = f.read()
        getpass = self.node.compile(source)
        # points = self.simulate(x)
        w = getpass.call('outside_link', self.challenge, self.gt, points, data)

        url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w, t=int(time.time() * 1000))
        response = self.session.get(url=url)
        print(response.text)


def general_register():
    url = 'https://www.geetest.com/demo/gt/register-click-official?t={}'.format(int(time.time() * 1000))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }
    response = requests.get(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)
    return data['challenge'], data['gt']


def main():
    challenge, gt = general_register()
    print(challenge, gt)
    GeetestCrack(challenge, gt).start()


if __name__ == '__main__':
    main()
