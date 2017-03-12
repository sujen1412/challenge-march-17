# Export Solr Index (Crawl) to ElasticSearch Index (CDR)

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from hashlib import sha256
from urlparse import urlparse
from SolrServer import SolrServer
from ESServer import ESServer


def url_doc_map(solr_docs):
    url_doc = {}
    for doc in solr_docs:
        url_doc[doc['url']] = doc
    return url_doc


def stored_url(url, content):
    hostname = urlparse(url).netloc
    rev = hostname.split(':')[0].split('.')[::-1]
    return '/'.join(rev) + '/' + sha256(content.encode('utf8')).hexdigest().upper()


def cdr_object(objects):
    objs = []
    for o in objects:
        obj = dict()
        obj['obj_original_url'] = o['url']
        obj['obj_stored_url'] = stored_url(o['url'], o['raw_content'])
        obj['content_type'] = o['content_type']
        obj['timestamp_crawl'] = o['fetch_timestamp']
        objs.append(obj)
    return objs


def cdr_doc_id(url, timestamp):
    return sha256(url + '-' + timestamp + '-jpl').hexdigest().upper()


def solr_to_cdr(parent, children):
    doc = dict()
    doc['content_type'] = parent['content_type']
    doc['crawler'] = parent['crawler']
    doc['raw_content'] = parent['raw_content']
    doc['team'] = 'jpl'
    doc['timestamp_crawl'] = parent['fetch_timestamp']
    doc['url'] = parent['url']
    doc['version'] = 3.0
    doc['id'] = cdr_doc_id(parent['url'], parent['fetch_timestamp'])
    doc['objects'] = cdr_object(children)
    return doc


def main(args):
    solr = SolrServer(args['solr'])
    #es = ESServer(args['elasticsearch'])

    html_docs = solr.search('cdr_status:NOT_INDEXED AND doc_type:webpage', fl='id,url,outlinks', rows=1000)
    obj_docs = solr.search('cdr_status:NOT_INDEXED AND doc_type:object', fl='id,url,content_type,fetch_timestamp,raw_content', rows=3000)
    html_url_docs = url_doc_map(html_docs)
    obj_url_docs = url_doc_map(obj_docs)
    indexed_docs = []
    c = 0
    cdr_docs = []

    for doc in html_docs:
        obj_children = []
        is_complete = True
        if 'outlinks' not in doc:
            continue
        for url in doc['outlinks']:
            if url not in html_url_docs and url not in obj_url_docs:
                is_complete = False
                break
            else:
                if url in obj_url_docs:
                    obj_children.append(obj_url_docs[url])
                # Check for documents that are not from the same host. We need to index them as well

        # Convert to CDRv3 format
        if is_complete and len(obj_children) > 0:
            c += 1
            # Prepare CDR Doc
            complete_doc = solr.search('id:' + doc['id'])[0]
            indexed_docs.append(complete_doc)  # To update document status
            cdr_doc = solr_to_cdr(complete_doc, obj_children)
            #print(str(cdr_doc) + "\n\n")
            cdr_docs.append(cdr_doc)
            # Push it to Elasticsearch
            if c == 100:
                #es.upload(cdr_docs)
                c = 0
                cdr_docs = []

    #if len(cdr_docs) > 0:
        #es.upload(cdr_docs)

    # Update Status of documents
    #solr.update_status(indexed_docs, 'INDEXED')


class ArgParser(ArgumentParser):
    def __init__(self):
        super(ArgParser, self).__init__(prog='Export to CDR',
            description="Utility to export Solr Documents to Elasticseach in CDRv3 format.",
            formatter_class=ArgumentDefaultsHelpFormatter,
            version="1.0")
        self.add_argument("-s", "--solr", help="Solr URL.")
        self.add_argument("-e", "--elasticsearch", help="Elasticsearch URL.")


if __name__ == '__main__':
    args = vars(ArgParser().parse_args())
    main(args)