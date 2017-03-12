from elasticsearch import Elasticsearch
from elasticsearch import helpers


class ESServer(object):
    def __init__(self, url):
        """
        Initialize ES Server
        :param url: ES URL
        """
        self.server = Elasticsearch([url])
        self.batch = 100
        self.index = ''

    def upload(self, docs):
        actions = []
        for doc in docs:
            doc_id = doc['id']
            del doc['id']
            action = {
                "_index": self.index,
                "_type": "doc",
                "_id": doc_id,
                "_source": doc
            }
            actions.append(action)
        helpers.bulk(self.server, actions)

    def commit(self):
        self.server.commit()
        pass
