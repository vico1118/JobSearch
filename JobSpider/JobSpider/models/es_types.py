from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

connections.create_connection(hosts=["localhost"])


class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class LagouType(DocType):
    # 拉钩数据类型
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word')
    url = Keyword()
    url_object_id = Keyword()
    salary = Text(analyzer='ik_max_word')
    job_city = Text(analyzer='ik_max_word')
    work_years = Text(analyzer='ik_max_word')
    degree_need = Text(analyzer='ik_max_word')
    job_type = Text(analyzer='ik_max_word')
    publish_time = Text()
    job_advantage = Text(analyzer='ik_max_word')
    job_desc = Text(analyzer='ik_max_word')
    job_addr = Text(analyzer='ik_max_word')
    company_name = Text(analyzer='ik_max_word')
    company_url = Keyword()
    tags = Text(analyzer='ik_max_word')
    crawl_time = Date()

    class Meta:
        index = 'lagou'
        doc_type = 'job'


class ShixisengType(DocType):
    # 实习僧数据类型
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word')
    url = Keyword()
    url_object_id = Keyword()
    salary = Text(analyzer='ik_max_word')
    job_city = Text(analyzer='ik_max_word')
    work_days = Text(analyzer='ik_max_word')
    degree_need = Text(analyzer='ik_max_word')
    shixi_needed = Text(analyzer='ik_max_word')
    publish_time = Text()
    job_advantage = Text(analyzer='ik_max_word')
    job_desc = Text(analyzer='ik_max_word')
    job_addr = Text(analyzer='ik_max_word')
    company_name = Text(analyzer='ik_max_word')
    company_url = Keyword()
    crawl_time = Date()

    class Meta:
        index = 'shixiseng'
        doc_type = 'job'


class QianchengType(DocType):
    # 51job数据类型
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word')
    url = Keyword()
    url_object_id = Keyword()
    salary = Text(analyzer='ik_max_word')
    job_city = Text(analyzer='ik_max_word')
    work_years = Text(analyzer='ik_max_word')
    degree_need = Text(analyzer='ik_max_word')
    people_need = Text(analyzer='ik_max_word')
    publish_time = Text()
    job_advantage = Text(analyzer='ik_max_word')
    job_desc = Text(analyzer='ik_max_word')
    job_addr = Text(analyzer='ik_max_word')
    company_name = Text(analyzer='ik_max_word')
    company_url = Keyword()
    crawl_time = Date()

    class Meta:
        index = 'qiancheng'
        doc_type = 'job'


if __name__ == '__main__':
    # 初始化数据库
    # LagouType.init()
    # ShixisengType.init()
    QianchengType.init()
