#from solr import Solr
from pysolr import Solr

class SolrServer(object):
    def __init__(self, url):
        """
        Initialize Solr Server
        :param url: Solr URL
        """
        self.server = Solr(url)
        self.batch = 100


    def search(self, query, **kwargs):
        """
        Query Solr
        :param query: search string
        :param kwargs: other Solr arguments
        :return: list of results
        """
        print('Querying Solr for: ' + query)
        response = self.server.search(query, None, **kwargs)
        print('Number of rows selected: ' + str(len(response.docs)))
        return response.docs

    def update_status(self, docs, status):
        """
        Update document status
        :param doc_id: Unique identifier of a document
        :param status: Document Status (Eg: IN_CDR)
        :return: true/false based on document update
        """
        self.server.add(docs, fieldUpdates={'cdr_status': status})
        pass

    def mark_cdr_indexed(ids_list, solr_url, core):
        solr_url = solr_url + core + "/update"
        update_docs = []
        for id in ids_list:
            timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
            doc = {"id":id, "cdr_status":{"set":"CDR_INDEXED"}}
            update_docs.append(doc)
        print json.dumps(update_docs)
        response = requests.post(solr_url, data=json.dumps(update_docs), headers={"content-type": "application/json"})
        return response

    def commit(self):
        self.server.commit()
        pass
