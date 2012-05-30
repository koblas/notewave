#!/usr/bin/python

import json
import urllib, urllib2

class ElasticException(Exception) :
    pass

class ElasticSearch(object) :
    class RestRequest(urllib2.Request) :
        def __init__(self, url, data=None, method=None) :
            urllib2.Request.__init__(self, url, data)
            self._method = method

        def get_method(self) :
            return self._method or urllib2.Request.get_method(self)

    @staticmethod
    def quote(str) :
        return str.replace('!', '\\!')

    def __init__(self, index, urlbase = None) :
        self._urlbase = urlbase or 'http://localhost:9200'
        self._index   = index

    def get(self, type, id) :
        url = "/".join([self._urlbase, self._index, type, str(id)])
        d = self._urlread(url)
        if d :
            print d['_source']
        return None

    def delete(self, type, id) :
        url = "/".join([self._urlbase, self._index, type, str(id)])
        d = self._urlread(url, method="DELETE")
        return d['ok']

    def delete_index(self) :
        url = "/".join([self._urlbase, self._index])
        d = self._urlread(url, method="DELETE")
        return d['ok']

    def put(self, type, id, data) :
        jdata = json.dumps(data)
        url = "/".join([self._urlbase, self._index, type, str(id)])
        d = self._urlread(url, data=jdata, method="PUT")
        return d['ok']

    def count(self, query, type=None) :
        if type :
            url = "/".join([self._urlbase, self._index, type, "_count"])
        else :
            url = "/".join([self._urlbase, self._index, "_count"])

        jdata = json.dumps(query)
        d = self._urlread(url, data=jdata, method="POST")

        return d['count']

    def search(self, query, type=None) :
        if type :
            url = "/".join([self._urlbase, self._index, type, "_search"])
        else :
            url = "/".join([self._urlbase, self._index, "_search"])

        jdata = json.dumps(query)
        d = self._urlread(url, data=jdata, method="POST")

        return d['hits']

    def _urlread(self, url, data=None, method="GET") :
        try :
            res = urllib2.urlopen(self.RestRequest(url, method=method, data=data))
            return json.loads(res.read())
        except urllib2.HTTPError, error: 
            if error.code == 404 :
                print error.read()
                # Not found
                return None

            try :
                s = error.read()
                print s
                d = error.read()
            except :
                raise
            raise ElasticException(d['error'])

if __name__ == '__main__' :
    es = ElasticSearch('twitter')
    es.put('tweet', 1, {
        'user'     : 'kimchy',
        'postDate' : '2009-11-15T14:12:12',
        'message'  : 'trying out Elastic Search',
    })
    es.put('tweet', 2, {
        'user'     : 'kimchy',
        'postDate' : '2009-11-15T14:12:12',
        'message'  : 'trying out Elastic Search',
    })
    #print es.count({'term':{'user':'kimchy'}})
    print es.search({'query':{'term':{'user':'kimchy'}}})
    es.get('tweet', 2)
    es.get('tweet', 4)
    #es.delete('tweet', 4)
    #es.delete('tweet', 2)
