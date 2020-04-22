# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import json
import re

import redis
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags

from models.es_types import LagouType, ShixisengType, QianchengType
from elasticsearch_dsl.connections import connections

# es = connections.create_connection(LagouType._doc_type.using)
# es = connections.create_connection(ShixisengType._doc_type.using)
es = connections.create_connection(QianchengType._doc_type.using)

redis_cli = redis.StrictRedis(host='localhost', port=6379)

class JobspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def gen_suggests(index, info_tuple):
    # 根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer='ik_max_word', params={'filter':['lowercase']}, body=text)
            analyzed_words = set([r['token'] for r in words['tokens'] if len(r['token']) > 1])
            new_words = analyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({'input': list(new_words), 'weight': weight})
            used_words = used_words.union(new_words)

    return suggests


def remove_lagou_splash(value):
    return value.replace('/', '')


def remove_lagou_publish_word(value):
    words = value.split()
    return words[0]


def handle_lagou_jobaddr(value):
    addr_list = value.split('\n')
    addr_list = [item.strip() for item in addr_list if item.strip() != '查看地图']
    return ''.join(addr_list)


class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_lagou_splash)
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(remove_lagou_splash)
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_lagou_splash)
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field(
        input_processor=MapCompose(remove_lagou_publish_word)
    )
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_lagou_jobaddr)
    )
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    tags = scrapy.Field(
        input_processor=Join(',')
    )
    crawl_time = scrapy.Field()

    def save_to_es(self):
        lagou = LagouType()
        lagou.title = self['title']
        lagou.url = self['url']
        lagou.url_object_id = self['url_object_id']
        lagou.salary = self['salary']
        lagou.job_city = self['job_city']
        lagou.work_years = self['work_years']
        lagou.degree_need = self['degree_need']
        lagou.job_type = self['job_type']
        lagou.publish_time = self['publish_time']
        lagou.job_advantage = self['job_advantage']
        lagou.job_desc = remove_tags(self['job_desc'])
        lagou.job_addr = self['job_addr']
        lagou.company_name = self['company_name']
        lagou.company_url = self['company_url']
        if 'tags' in self:
            lagou.tags = self['tags']
        lagou.crawl_time = self['crawl_time']
        lagou.suggest = gen_suggests(LagouType._doc_type.index, ((lagou.title, 10), (lagou.tags, 7), (lagou.job_desc, 5)))

        lagou.save()

        return


def handle_shixiseng_salary_value(value):
    if value == '面议':
        return value
    else:
        f = open('JobSpider/shixiseng_word/word.json', 'r')
        read = f.read()
        word_dict = json.loads(read)
        s = value.encode('unicode_escape').decode('utf-8')
        words = s.split('-')
        new_words = []
        for word in words:
            new_word = []
            objs = re.findall(r'.*?\\u([a-z0-9]{4})', word)
            for obj in objs:
                key = '0x' + obj
                if word_dict.get(key):
                    new_word.append(word_dict.get(key))
                elif key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'):
                    new_word.append('/')
                    new_word.append(key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'))
                else:
                    print('数据错误')
            new_words.append(''.join(new_word))
        f.close()
        result = '-'.join(new_words)
        return result


def handle_shixiseng_value(value):
    f = open('JobSpider/shixiseng_word/word.json', 'r')
    read = f.read()
    word_dict = json.loads(read)
    s = value.encode('unicode_escape').decode('utf-8')
    objs = re.findall(r'\\u([a-z0-9]{4})', s)
    new_word = []
    for obj in objs:
        key = '0x' + obj
        if word_dict.get(key):
            value = word_dict.get(key)
        elif key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'):
            value = key.replace('0x', r'\u').encode('utf8').decode('unicode_escape')
        else:
            print('数据错误')
        new_word.append(value)
    f.close()
    result = ''.join(new_word)
    return result


def handle_shixiseng_publish_time(value):
    f = open('JobSpider/shixiseng_word/word.json', 'r')
    read = f.read()
    word_dict = json.loads(read)
    s = value.encode('unicode_escape').decode('utf-8')
    words = s.split(' ')
    dates = words[0].split('-')
    times = words[1].split(':')
    new_dates = []
    new_times = []
    for date in dates:
        new_date = []
        objs = re.findall(r'.*?\\u([a-z0-9]{4})', date)
        for obj in objs:
            key = '0x' + obj
            if word_dict.get(key):
                new_date.append(word_dict.get(key))
            elif key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'):
                new_date.append(key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'))
            else:
                print('数据错误')
        new_dates.append(''.join(new_date))
    dates_result = '-'.join(new_dates)
    for time in times:
        new_time = []
        objs = re.findall(r'.*?\\u([a-z0-9]{4})', time)
        for obj in objs:
            key = '0x' + obj
            if word_dict.get(key):
                new_time.append(word_dict.get(key))
            elif key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'):
                new_time.append(key.replace('0x', r'\u').encode('utf8').decode('unicode_escape'))
            else:
                print('数据错误')
        new_times.append(''.join(new_time))
    times_result = ':'.join(new_times)
    f.close()
    return '{0} {1}'.format(dates_result, times_result)


def handle_shixiseng_company_name(value):
    word = value.replace('\n', '')
    return word


class ShixisengJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class ShixisengJobItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field(
        input_processor=MapCompose(handle_shixiseng_salary_value)
    )
    job_city = scrapy.Field()
    work_days = scrapy.Field(
        input_processor=MapCompose(handle_shixiseng_value)
    )
    degree_need = scrapy.Field()
    shixi_needed = scrapy.Field(
        input_processor=MapCompose(handle_shixiseng_value)
    )
    publish_time = scrapy.Field(
        input_processor=MapCompose(handle_shixiseng_publish_time)
    )
    job_advantage = scrapy.Field(
        input_processor=Join(',')
    )
    job_desc = scrapy.Field()
    job_addr = scrapy.Field()
    company_name = scrapy.Field(
        input_processor=MapCompose(handle_shixiseng_company_name)
    )
    company_url = scrapy.Field()
    crawl_time = scrapy.Field()

    def save_to_es(self):
        shixiseng = ShixisengType()
        shixiseng.title = self['title']
        shixiseng.url = self['url']
        shixiseng.url_object_id = self['url_object_id']
        shixiseng.salary = self['salary']
        shixiseng.job_city = self['job_city']
        shixiseng.work_days = self['work_days']
        shixiseng.degree_need = self['degree_need']
        shixiseng.shixi_needed = self['shixi_needed']
        shixiseng.publish_time = self['publish_time']
        shixiseng.job_advantage = self['job_advantage']
        shixiseng.job_desc = remove_tags(self['job_desc'])
        shixiseng.job_addr = self['job_addr']
        shixiseng.company_name = self['company_name']
        shixiseng.company_url = self['company_url']
        shixiseng.crawl_time = self['crawl_time']
        shixiseng.suggest = gen_suggests(ShixisengType._doc_type.index, ((shixiseng.title, 10), (shixiseng.job_desc, 5)))

        shixiseng.save()

        return


def handel_qiancheng_value(value):
    if '\xa0' in value:
        word = value.replace('\xa0', '')
        return word
    else:
        return value


class QianchengJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class QianchengJobItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(handel_qiancheng_value)
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(handel_qiancheng_value)
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(handel_qiancheng_value)
    )
    people_need = scrapy.Field(
        input_processor=MapCompose(handel_qiancheng_value)
    )
    publish_time = scrapy.Field(
        input_processor=MapCompose(handel_qiancheng_value)
    )
    job_advantage = scrapy.Field(
        input_processor=Join(',')
    )
    job_desc = scrapy.Field()
    job_addr = scrapy.Field()
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    crawl_time = scrapy.Field()

    def save_to_es(self):
        qiancheng = QianchengType()
        qiancheng.title = self['title']
        qiancheng.url = self['url']
        qiancheng.url_object_id = self['url_object_id']
        if 'salary' in self:
            qiancheng.salary = self['salary']
        qiancheng.job_city = self['job_city']
        qiancheng.work_years = self['work_years']
        qiancheng.degree_need = self['degree_need']
        qiancheng.people_need = self['people_need']
        qiancheng.publish_time = self['publish_time']
        if 'job_advantage' in self:
            qiancheng.job_advantage = self['job_advantage']
        qiancheng.job_desc = remove_tags(self['job_desc'])
        if 'job_addr' in self:
            qiancheng.job_addr = self['job_addr']
        qiancheng.company_name = self['company_name']
        qiancheng.company_url = self['company_url']
        qiancheng.crawl_time = self['crawl_time']
        qiancheng.suggest = gen_suggests(QianchengType._doc_type.index, ((qiancheng.title, 10), (qiancheng.job_desc, 5)))

        qiancheng.save()

        return

