import json
from datetime import datetime
from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from search.models import LagouType, ShixisengType, QianchengType
from elasticsearch import Elasticsearch
import redis

client = Elasticsearch(hosts=['127.0.0.1'])
redis_cli = redis.StrictRedis(host="localhost", charset="UTF-8", decode_responses=True)

# Create your views here.


class IndexView(View):
    def get(self, request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", '+inf', '-inf', start=0, num=5)
        return render(request, 'index.html', {'topn_search': topn_search})


class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        s_type = request.GET.get('s_type', '')
        re_datas = []
        if s_type == 'all':
            if key_words:
                s_suggest = {
                    'suggest': {
                        'my_suggest': {
                            'text': key_words, 'completion': {
                                'field': 'suggest', 'fuzzy': {
                                    'fuzziness': 2}, 'size': 10
                            }
                        }
                    }
                }
                suggestions = client.search(
                    index=["lagou", "shixiseng", "qiancheng"],
                    body=s_suggest
                )
                for suggest in suggestions['suggest']['my_suggest'][0]['options']:
                    source = suggest['_source']
                    re_datas.append(source['title'])

        if s_type == 'lagou':
            if key_words:
                s = LagouType.search()
                s = s.suggest('my_suggest', key_words, completion={
                    "field": "suggest", "fuzzy": {
                        "fuzziness": 2
                    },
                    "size": 10
                })
                suggestions = s.execute_suggest()
                for match in suggestions.my_suggest[0].options:
                    source = match._source
                    re_datas.append(source["title"])

        if s_type == 'shixiseng':
            if key_words:
                s = ShixisengType.search()
                s = s.suggest('my_suggest', key_words, completion={
                    "field": "suggest", "fuzzy": {
                        "fuzziness": 2
                    },
                    "size": 10
                })
                suggestions = s.execute_suggest()
                for match in suggestions.my_suggest[0].options:
                    source = match._source
                    re_datas.append(source["title"])

        if s_type == 'qiancheng':
            if key_words:
                s = QianchengType.search()
                s = s.suggest('my_suggest', key_words, completion={
                    "field": "suggest", "fuzzy": {
                        "fuzziness": 2
                    },
                    "size": 10
                })
                suggestions = s.execute_suggest()
                for match in suggestions.my_suggest[0].options:
                    source = match._source
                    re_datas.append(source["title"])

        return HttpResponse(json.dumps(re_datas), content_type='application/json')


class SearchView(View):
    def get(self, request):
        key_words = request.GET.get('q', '')
        s_type = request.GET.get('s_type', '')
        index_name = None
        source = None
        if s_type == 'all':
            index_name = ['lagou', 'shixiseng', 'qiancheng']
            source = 'all'
        if s_type == 'lagou':
            index_name = "lagou"
            source = 'lagou'
        if s_type == 'shixiseng':
            index_name = "shixiseng"
            source = 'shixiseng'
        if s_type == 'qiancheng':
            index_name = "qiancheng"
            source = 'qiancheng'

        redis_cli.zincrby('search_keywords_set', 1, key_words)
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", '+inf', '-inf', start=0, num=5)

        page = request.GET.get('p', '1')
        try:
            page = int(page)
        except:
            page = 1

        start_time = datetime.now()
        response = client.search(
            index=index_name,
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["tags", "title", "job_desc"]
                    }
                },
                "from": (page - 1) * 10,
                "size": 10,
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "tags": {},
                        "title": {},
                        "job_desc": {},
                    }
                }
            }
        )
        lagou = client.search(
            index="lagou",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["tags", "title", "job_desc"]
                    }
                }
            }
        )
        shixiseng = client.search(
            index="shixiseng",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["tags", "title", "job_desc"]
                    }
                }
            }
        )
        qiancheng = client.search(
            index="qiancheng",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["tags", "title", "job_desc"]
                    }
                }
            }
        )

        end_time = datetime.now()
        last_seconds = (end_time-start_time).total_seconds()

        lagou_count = lagou['hits']['total']
        shixiseng_count = shixiseng['hits']['total']
        qiancheng_count = qiancheng['hits']['total']

        total_nums = response["hits"]["total"]
        if (page % 10) > 0:
            page_nums = int(total_nums/10) + 1
        else:
            page_nums = int(total_nums/10)

        hit_list = []

        for hit in response["hits"]["hits"]:
            hit_dict = {}
            if "title" in hit["highlight"]:
                hit_dict["title"] = ''.join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = hit["_source"]["title"]
            if "job_desc" in hit["highlight"]:
                hit_dict["job_desc"] = ''.join(hit["highlight"]["job_desc"])[:500]
            else:
                hit_dict["job_desc"] = hit["_source"]["job_desc"][:500]

            hit_dict["publish_time"] = hit["_source"]["publish_time"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]
            if hit["_index"] == "lagou":
                hit_dict["source"] = '拉勾网'
            elif hit["_index"] == "shixiseng":
                hit_dict["source"] = '实习僧'
            elif hit["_index"] == "qiancheng":
                hit_dict["source"] = '51jobs'

            hit_list.append(hit_dict)

        return render(request, "result.html", {"page": page,
                                               "all_hits": hit_list,
                                               "key_words": key_words,
                                               "total_nums": total_nums,
                                               "page_nums": page_nums,
                                               "last_seconds": last_seconds,
                                               'lagou_count': lagou_count,
                                               'shixiseng_count': shixiseng_count,
                                               'qiancheng_count': qiancheng_count,
                                               'source': source,
                                               'index_name': index_name,
                                               'topn_search': topn_search})

