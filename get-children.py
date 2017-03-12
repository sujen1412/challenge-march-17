import re
import json
import argparse
import urllib
import urllib2


def makeOutlinkSet(data):
    pass


def fetchedOutOfDomainLinks(solr, core, rows):
    print "Getting fetched outlinks"
    query = {}
    query["q"] = "*:*"
    query['fl']="url"
    query['wt'] = "json"
    query['rows'] = int(rows)
    filter_query = "fq=!hostname:*yahoo.com&fq=!status_name:fetch_success"
    request_url = solr + core + "/select"
    start = 0
    outlink_set = set()
    end = 100
    while (start < end):
        print "Querying range {} to {}".format(start, end)
        query['start'] = start
        query_data = urllib.urlencode(query) + "&" + urllib.urlencode({"fq":"!hostname:*yahoo.com"}) \
                     + "&" + urllib.urlencode({"fq":"status_name:fetch_success"})

        req = urllib2.Request(request_url, query_data)
        response = urllib2.urlopen(req)
        data = json.loads(response.read())
        end = int(data["response"]["numFound"])
        for doc in data["response"]["docs"]:
            outlink_set.add(doc['url'])
        start = int(100) + int(start)
    return outlink_set


def getOutlinks(solr, core, rows):
    print "GEtting outlinks to fetch"
    query = {}
    query["q"] = "*:*"
    query['fl']="outlinks"
    query['wt'] = "json"
    query['rows'] = int(rows)
    request_url = solr + core + "/select"

    filter_query = "fq=hostname:*yahoo.com&fq=status_name:fetch_success&fq=cdr_status:NOT_INDEXED"
    start = 0
    outlink_set = set()
    end = 100
    while (start < end):
        print "Querying range {} to {}".format(start, end)
        query['start'] = start
        query_data = urllib.urlencode(query) + "&" + str(filter_query)
        req = urllib2.Request(request_url, query_data)
        response = urllib2.urlopen(req)
        data = json.loads(response.read())
        end = int(data["response"]["numFound"])
        for doc in data["response"]["docs"]:
            if 'outlinks' in doc:
                for url in doc['outlinks']:
                    if not re.match("^http.*://.*yahoo.com.*", url):
                        outlink_set.add(url)

        start = int(100) + int(start)

    return outlink_set


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_file", default="outlinks.txt")
    parser.add_argument("--core", default="sparkler")
    parser.add_argument("--solr", default="http://localhost:8986/solr/", required=True)
    parser.add_argument("--rows", default=100)
    args = parser.parse_args()

    unfetched = getOutlinks(args.solr, args.core, args.rows)
    fetched = fetchedOutOfDomainLinks(args.solr, args.core, args.rows)
    common = unfetched.intersection(fetched)
    remain = unfetched - fetched
    with open(args.output_file, 'w') as fw:
        for url in remain:
            fw.write(str(url.encode('utf-8')) + "\n")

