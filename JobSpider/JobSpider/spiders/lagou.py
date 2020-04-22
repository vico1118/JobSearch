# -*- coding: utf-8 -*-
from datetime import datetime

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from items import LagouJobItem, LagouJobItemLoader
from utils.common import get_md5


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['http://www.lagou.com/']

    custom_settings = {
        'COOKIES_ENABLED': False,
        'AUTOTHROTTLE_ENABLED': False,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_DELAY': 10,
    }

    rules = (
        Rule(LinkExtractor(allow=r'zhaopin/.*'), follow=True),
        Rule(LinkExtractor(allow=r'gongsi/j\d+.html'), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),
    )

    def parse_job(self, response):
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()

        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css('title', '.job-name::attr(title)')
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_css('salary', '.job_request .salary::text')
        item_loader.add_xpath('job_city', '//*[@class="job_request"]/h3/span[2]/text()')
        item_loader.add_xpath('work_years', '//*[@class="job_request"]/h3/span[3]/text()')
        item_loader.add_xpath('degree_need', '//*[@class="job_request"]/h3/span[4]/text()')
        item_loader.add_xpath('job_type', '//*[@class="job_request"]/h3/span[5]/text()')
        item_loader.add_css('tags', '.position-label li::text')
        item_loader.add_css('publish_time', '.publish_time::text')
        item_loader.add_css('job_advantage', '.job-advantage p::text')
        item_loader.add_css('job_desc', '.job_bt div')
        item_loader.add_css('job_addr', '.work_addr')
        item_loader.add_css('company_name', '#job_company dt a img::attr(alt)')
        item_loader.add_css('company_url', '#job_company dt a::attr(href)')
        item_loader.add_value('crawl_time', datetime.now())
        lagou_item = item_loader.load_item()

        return lagou_item

