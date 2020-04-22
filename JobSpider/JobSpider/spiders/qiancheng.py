# -*- coding: utf-8 -*-
import re
from datetime import datetime
from urllib.parse import urlsplit

import scrapy

from items import QianchengJobItem, QianchengJobItemLoader
from utils.common import get_md5


class QianchengSpider(scrapy.Spider):
    name = 'qiancheng'
    allowed_domains = ['www.51job.com', 'search.51job.com', 'jobs.51job.com']
    start_urls = ['https://search.51job.com/list/030200,000000,0000,00,9,99,%2B,2,1.html']

    custom_settings = {
        'COOKIES_ENABLED': False,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_DELAY': 5,
    }

    def parse(self, response):
        jobs = response.css('#resultList .el p')
        for job in jobs:
            job_url = job.css('span a::attr(href)').extract_first('')
            yield scrapy.Request(url=job_url, callback=self.parse_detail)

        parse_url = urlsplit(response.url)
        path = parse_url.path
        get_num = re.match(r'.*,(\d+).html', path)
        num = get_num.group(1)
        new_num = int(num) + 1
        if new_num < 1000:
            next_url = 'https://search.51job.com/list/030200,000000,0000,00,9,99,%2B,2,{0}.html'.format(new_num)
            yield scrapy.Request(url=next_url, callback=self.parse)
        else:
            self.crawler.engine.close_spider(reason='cancelled')

    def parse_detail(self, response):
        item_loader = QianchengJobItemLoader(item=QianchengJobItem(), response=response)
        item_loader.add_css('title', '.in .cn h1::attr(title)')
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_css('salary', '.in .cn strong::text')
        detail = response.css('.in .cn .msg.ltype::text').extract()
        if len(detail) < 5:
            item_loader.add_value('job_city', detail[0])
            item_loader.add_value('work_years', detail[1])
            item_loader.add_value('degree_need', '无学历要求')
            item_loader.add_value('people_need', detail[2])
            item_loader.add_value('publish_time', detail[3])
        else:
            item_loader.add_value('job_city', detail[0])
            item_loader.add_value('work_years', detail[1])
            item_loader.add_value('degree_need', detail[2])
            item_loader.add_value('people_need', detail[3])
            item_loader.add_value('publish_time', detail[4])
        item_loader.add_css('job_advantage', '.in .cn .jtag .t1 span::text')
        item_loader.add_css('job_desc', '.bmsg.job_msg.inbox')
        item_loader.add_xpath('job_addr', '//div[@class="bmsg inbox"]/p[1]/text()')
        item_loader.add_css('company_name', '.com_msg .com_name p::text')
        item_loader.add_css('company_url', '.com_msg .com_name::attr(href)')
        item_loader.add_value('crawl_time', datetime.now())
        qiancheng_item = item_loader.load_item()

        return qiancheng_item

