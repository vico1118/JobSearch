# -*- coding: utf-8 -*-
from datetime import datetime

import scrapy
from scrapy import Request
from urllib.parse import urlsplit, parse_qsl, urljoin
import json

from items import ShixisengJobItem, ShixisengJobItemLoader
from utils.common import get_md5


class ShixisengSpider(scrapy.Spider):
    name = 'shixiseng'
    allowed_domains = ['www.shixiseng.com/']
    start_urls = ['https://www.shixiseng.com/app/interns/search/v2?page=1&keyword=&type=intern&area=&months=&days=&degree=&official=&enterprise=&salary=-0&publishTime=&sortType=&city=%E5%85%A8%E5%9B%BD&internExtend=']

    custom_settings = {
        'COOKIES_ENABLED': False,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_DELAY': 5,
    }

    def parse(self, response):
        parse_url = urlsplit(response.url)
        query = parse_url.query
        page = parse_qsl(query)[0][1]
        new_page = int(page) + 1
        if new_page < 251:
            json_data = json.loads(response.text)
            for data in json_data['msg']['data']:
                post_url = data['uuid']
                yield scrapy.Request(url=urljoin('https://www.shixiseng.com/intern/', post_url),
                                     callback=self.parse_detail, dont_filter=True)

            next_url = 'https://www.shixiseng.com/app/interns/search/v2?page={0}&keyword=&type=intern&area=&months=&days=&degree=&official=&enterprise=&salary=-0&publishTime=&sortType=&city=%E5%85%A8%E5%9B%BD&internExtend='.format(new_page)
            yield scrapy.Request(url=next_url, callback=self.parse, dont_filter=True)
        else:
            self.crawler.engine.close_spider(reason='cancelled')

    def parse_detail(self, response):
        item_loader = ShixisengJobItemLoader(item=ShixisengJobItem(), response=response)
        item_loader.add_css('title', '.job-header .new_job_name span::text')
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_css('salary', '.job_money.cutom_font::text')
        item_loader.add_css('job_city', '.job_msg .job_position::attr(title)')
        item_loader.add_css('work_days', '.job_msg .job_week.cutom_font::text')
        item_loader.add_css('degree_need', '.job_msg .job_academic::text')
        item_loader.add_xpath('shixi_needed', '//div[@class="job_msg"]/span[5]/text()')
        item_loader.add_css('publish_time', '.job_date .cutom_font::text')
        item_loader.add_css('job_advantage', '.job_good_list span::text')
        item_loader.add_xpath('job_desc', '//div[@class="content_left"]/div[1]')
        item_loader.add_css('job_addr', '.con-job.job_city .com_position::text')
        item_loader.add_css('company_name', '.com-name::text')
        company_post_url = response.css('.com-name::attr(href)').extract_first()
        item_loader.add_value('company_url', 'www.shixiseng.com{}'.format(company_post_url))
        item_loader.add_value('crawl_time', datetime.now())
        shixiseng_item = item_loader.load_item()

        return shixiseng_item


