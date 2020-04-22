import requests
from lxml import etree
import re
import json
import base64
from fontTools.ttLib import TTFont


class shixiceng_word():
    # 每次爬取实习僧都抓取一次
    def __init__(self):
        url = 'https://www.shixiseng.com/intern/inn_q53wbbchaqzv'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
        }
        self.respone = requests.get(url, headers=headers)

    def get_dict(self):
        # 获取实习僧反爬字体的文件
        # r = requests.get('https://www.shixiseng.com/interns/iconfonts/file')
        # print(r.content)
        # with open('a.ttf', 'wb') as f:
        #     f.write(r.content)
        # font = TTFont('a.ttf')
        # font.saveXML('a.xml')
        if self.respone.status_code == 200:
            html = etree.HTML(self.respone.text)
            result = html.xpath('string(/html/head/style[2]/text())')
            match_obj = re.match(r'.*?(data.*)"', result, re.DOTALL)
            result = match_obj.group(1)
            code = result.replace('data:application/octet-stream;base64,', '')
            with open('word.ttf', 'wb') as f:
                f.write(base64.b64decode(code))
            font = TTFont('word.ttf')
            font.saveXML('word.xml')
        else:
            print('请更换网址爬取')

    def save_dict(self):
        # 把文件数据抽取出来作为字典
        with open('word.xml') as f:
            xml = f.read()
        keys = re.findall('<map code="(0x.*?)" name="uni.*?"/>', xml)[:99]
        values = re.findall('<map code="0x.*?" name="uni(.*?)"/>', xml)[:99]
        for i in range(len(values)):
            if len(values[i]) < 4:
                values[i] = ('\\u00' + values[i]).encode('utf-8').decode('unicode_escape')
            else:
                values[i] = ('\\u' + values[i]).encode('utf-8').decode('unicode_escape')
        word_dict = dict(zip(keys, values))
        with open('word.json', 'w') as f:
            word_dict = json.dumps(word_dict)
            f.write(word_dict)


if __name__ == '__main__':
    word = shixiceng_word()
    word.get_dict()
    word.save_dict()

