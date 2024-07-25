"""
챗봇 API 입니다.
"""

import json
import requests
import datetime as dt
from flask import Flask, request, abort
from src.config import Config as config
from src.utils import *

app = Flask(__name__)


## elastic 연동 -> 추후 모듈 분리 ㅠ

from elasticsearch import Elasticsearch
from langchain.chat_models import ChatOpenAI
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings.openai import OpenAIEmbeddings

es_client = Elasticsearch(
    hosts=config.ELASTICSEARCH_HOSTS.split(","),
    max_retries=10
)
print("ES info: ", pretty_json(Elasticsearch.info(es_client)))

## elasticsearch 내의 모든 인덱스
indices = es_client.indices.get_alias("*")

for index in indices:
    print(index)

def get_mapping(param: dict):
    return es_client.indices.get_mapping(param['index'])

# kibana 를 통해 받은 샘플 데이터. => ecommerce 샘플.
mapping = get_mapping({"index": "kibana_sample_data_ecommerce"})
# print(pretty_json(mapping))


from langchain.prompts import ChatPromptTemplate

template = """Based on the index mapping below,
write a query for ElasticSearch that would answer the user's question:

{mapping}

Question: {question}
query: """

chat_prompt_template = ChatPromptTemplate.from_template(template)

from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.chat_models import ChatOpenAI

chat_model = ChatOpenAI()

query_gen_chain = (
    RunnablePassthrough.assign(mapping=get_mapping)
    | chat_prompt_template
    | chat_model
    | StrOutputParser()
)

response = query_gen_chain.invoke({"index": "kibana_sample_data_ecommerce", "question": "하루 주문량이 가장 많은 날짜가 언제지? 주문량이 같은 경우에는 가장 최근 날짜로 알려줘."})
print(response)

print(pretty_json(es_client.search(body=response)))

full_template = """Based on the table schema below, question, sql query, and sql response, write a natural language response in Korean:
{mapping}

Question: {question}
Query: {query}
Response: {response}"""

chat_prompt_response = ChatPromptTemplate.from_template(full_template)

full_chain = (
    RunnablePassthrough.assign(query=query_gen_chain)
    | RunnablePassthrough.assign(
        mapping = get_mapping,
        response = lambda x : es_client.search(body=x['query']),
    )
    | chat_prompt_response
    | chat_model
    | StrOutputParser()
)

answer = full_chain.invoke({"index": "kibana_sample_data_ecommerce", "question": "하루 주문량이 가장 많은 날짜가 언제지? 주문량이 같은 경우에는 가장 최근 날짜로 알려줘."})
# print(answer)

# embedding = OpenAIEmbeddings()


# 최초 웹 루트 접속 경로
@app.route('/', methods=['GET'])
def index():
    test = request.get_json(silent=True)
    print(test)

    answer = full_chain.invoke({"index": "kibana_sample_data_ecommerce", "question": "하루 주문량이 가장 많은 날짜가 언제지? 주문량이 같은 경우에는 가장 최근 날짜로 알려줘."})
    print(answer)
    return '''<div>
    <ul>
      <li>{answer}</li>
    </ul>
    </div>
    '''

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")