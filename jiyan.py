import time
import requests
import json
import execjs
from PIL import Image, ImageChops
from ImageHandle import handle, calculate_x
import logging


def register():
    url = 'http://www.geetest.com/type/gt/register?type=1'
    response = session.get(url=url, headers=headers)
    data = json.loads(response.text)
    return data['gt'], data['challenge']


def gettype():
    url = 'http://api.geetest.com/gettype.php'
    response = session.get(url=url, headers=headers, params={'gt': gt})


def get_and_ajax():
    with open('fullpage.js', 'r', encoding='utf-8') as f:
        source = f.read()

    getpass = node.compile(source)
    E, w_get = getpass.call('outside_link', challenge, gt)

    get_url = 'http://api.geetest.com/get.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}'.format(gt=gt, challenge=challenge, lang='zh-cn', w=w_get)
    get_response = session.get(url=get_url, headers=headers)
    data = json.loads(get_response.text[1: -1])['data']

    with open('fullpage2.js', 'r', encoding='utf-8') as f:
        source = f.read()

    getpass = node.compile(source)
    w_ajax = getpass.call('outside_link', challenge, gt, E, data)

    ajax_url = 'http://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}'.format(gt=gt, challenge=challenge, lang='zh-cn', w=w_ajax)
    response = session.get(url=ajax_url, headers=headers)
    return json.loads(response.text[1: -1])


def api_get():
    url = 'http://api.geetest.com/get.php'
    params = {
        'is_next': 'true',
        'type': 'slide3',
        'gt': gt,
        'challenge': challenge,
        'lang': 'zh-cn',
        'https': 'false',
        'protocol': 'http://',
        'offline': 'false',
        'product': 'popup',
        'api_server': 'api.geetest.com',
        'width': '100%',
        'callback': 'geetest',
    }
    response = session.get(url=url, headers=headers, params=params)
    data = json.loads(response.text[8: -1])
    return data


def get_image(data):
    bg_url = 'http://static.geetest.com/' + data['bg']
    bg_response = session.get(url=bg_url, headers=headers)
    with open('bg.jpg', 'wb') as f:
        f.write(bg_response.content)

    fullbg_url = 'http://static.geetest.com/' + data['fullbg']
    fullbg_response = session.get(url=fullbg_url, headers=headers)
    with open('fullbg.jpg', 'wb') as f:
        f.write(fullbg_response.content)

    bg = handle(Image.open('bg.jpg'))
    fullbg = handle(Image.open('fullbg.jpg'))

    image = ImageChops.difference(fullbg, bg)
    image = image.point(lambda x: 255 if x > 80 else 0)
    image = image.resize((260, 160), Image.ANTIALIAS)
    image.save('diff.jpg')
    return calculate_x(image)


def api_ajax(x, data):
    with open('slide.js', 'r', encoding='utf-8') as f:
        source = f.read()

    getpass = node.compile(source)
    w = getpass.call('outside_link', x, data)

    url = 'http://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}'.format(gt=data['gt'], challenge=data['challenge'], lang='zh-cn', w=w)
    response = session.get(url=url, headers=headers)
    return json.loads(response.text[1: -1])


if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        'Referer': 'http://www.geetest.com/type/',
    }
    res_matters = {
        'success': '滑动验证成功！',
        'fail': '滑动验证失败！',
        'forbidden': '模拟滑动轨迹不合适！',
    }
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )
    session = requests.Session()
    node = execjs.get('Node')

    logging.info('开始滑动验证！')
    gt, challenge = register()
    gettype()
    res1 = get_and_ajax()
    print(res1)

    api_get_result = api_get()
    slider_x = get_image(api_get_result)
    logging.info('滑块到达位置：{x}'.format(x=slider_x))
    time.sleep(1)

    if slider_x:
        res2 = api_ajax(slider_x, api_get_result)
        print(res2)
        message = res_matters.get(res2.get('message'))
        if message:
            logging.info(message)
        else:
            logging.warning('未知错误！')

    else:
        logging.warning('滑块拟到达位置无法确定！')
