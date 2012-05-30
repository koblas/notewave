'''
Python Oauth client for Twitter

Used the SampleClient from the OAUTH.org example python client as basis.

props to leahculver for making a very hard to use but in the end usable oauth lib.

'''
import logging
import httplib
import urllib
import time
import webbrowser
import oauth as oauth
from urlparse import urlparse, urlsplit

class CommonOAuthClient(oauth.OAuthClient) :
    def __init__(self, consumer_key, consumer_secret, oauth_token=None, oauth_token_secret=None):
        self.sha1_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.consumer    = oauth.OAuthConsumer(consumer_key, consumer_secret)

        if (oauth_token != None) and (oauth_token_secret!=None) :
            self.token = oauth.OAuthConsumer(oauth_token, oauth_token_secret)
        else:
            self.token = None

    def oauth_request(self, url, args = None, method = None, postdata = None):
        if not method :
            if not args and not postdata :
                method = "GET"
            else :
                method = "POST"
        req = oauth.OAuthRequest.from_consumer_and_token(self.consumer, self.token, method, url, args)
        req.sign_request(self.sha1_method, self.consumer, self.token)

        if method == 'GET' : 
            return self.http_wrapper(method, req.to_url())
        elif method == 'POST' :
            if postdata :
                return self.http_wrapper(method, req.to_url(), postdata)
            else : 
                return self.http_wrapper(method, req.get_normalized_http_url(), req.to_postdata())

    #
    # this is barely working. (i think. mostly it is that everyone else is using httplib) 
    #
    def http_wrapper(self, method, url, postdata = None, headers={}): 
        logging.debug('OAuth URL : %s' % url)
        logging.debug('OAuth Data : %s' % str(postdata))

        urlinfo = urlsplit(url)

        if urlinfo[0] == 'http' :
            client = httplib.HTTPConnection(urlinfo[1])
        elif urlinfo[0] == 'https' :
            client = httplib.HTTPSConnection(urlinfo[1])

        if 'User-Agent' not in headers :
            headers['User-Agent'] = 'OAuth Python Client Library'


        if method == 'POST' :
            headers['Content-type'] = 'application/x-www-form-urlencoded'
            headers['Content-Length'] = len(postdata)
            #print headers
            client.request('POST', urlinfo[2], postdata, headers)
        elif urlinfo[3] == '' or urlinfo == None :
            client.request('GET', urlinfo[2], None, headers)
        else :
            client.request('GET', urlinfo[2]+'?'+urlinfo[3], None, headers)

        response = client.getresponse()

        data = response.read()

        if response.status != 200 :
            #print response.getheaders()
            #print data
            raise Exception("HTTP Status: %d -- message: %s" % (response.status, data))
        client.close()
        return data

    def oauth_parse_response(self, response_string):
        r = {}
        for param in response_string.split("&"):
            pair = param.split("=")
            if len(pair) != 2 :
                break
                
            r[pair[0].strip()] = urllib.unquote(pair[1])
        return r

    def get_request_token(self, cburl=None, method="POST"):
        if cburl :
            response = self.oauth_request(self.request_token_url(), {'oauth_callback' : cburl}, method=method)
        else :
            response = self.oauth_request(self.request_token_url(), method=method)

        token = self.oauth_parse_response(response)
        try:
            self.token = oauth.OAuthConsumer(token['oauth_token'],token['oauth_token_secret'])
            return token
        except:
            raise oauth.OAuthError('Invalid oauth_token')

    def get_authorize_url(self, token, callback=None):
        url = self.authorize_url() + '?oauth_token=' + urllib.quote(token)
        if callback :
            url += '&oauth_callback=' + urllib.quote(callback)
        return url

    def get_access_token(self, token=None, verifier=None, params={}):
        if token :
            params['oauth_token'] = token
        if verifier :
            params['oauth_verifier'] = verifier

        #print params

        if len(params) != 0 :
            r = self.oauth_request(self.access_token_url(), params)
        else :
            r = self.oauth_request(self.access_token_url())
        #print r
        token = self.oauth_parse_response(r)
        self.token = oauth.OAuthConsumer(token['oauth_token'],token['oauth_token_secret'])
        return token

class GoogleOAuthClient(CommonOAuthClient) :
    api_root_url  = 'https://www.google.com' #for testing 'http://term.ie'
    api_root_port = "443"

    #set api urls
    def request_token_url(self):
        return self.api_root_url + '/accounts/OAuthGetRequestToken'

    def authorize_url(self):
        return self.api_root_url + '/accounts/OAuthAuthorizeToken'

    def access_token_url(self):
        return self.api_root_url + '/accounts/OAuthGetAccessToken'

    def get_request_token(self, cburl=None):
        response = self.oauth_request(self.request_token_url(), {'scope' : 'http://www.google.com/m8/feeds'})
        token = self.oauth_parse_response(response)
        try:
            self.token = oauth.OAuthConsumer(token['oauth_token'], token['oauth_token_secret'])
            return token
        except:
            raise oauth.OAuthError('Invalid oauth_token')

#
#
#
class YahooOAuthClient(CommonOAuthClient):
    api_root_url  = 'https://api.login.yahoo.com'
    api_root_port = "443"

    def __init__(self, consumer_key, consumer_secret, oauth_token=None, oauth_token_secret=None):
        super(YahooOAuthClient, self).__init__(consumer_key, consumer_secret, oauth_token, oauth_token_secret)
        #self.sha1_method = oauth.OAuthSignatureMethod_PLAINTEXT()

    #set api urls
    def request_token_url(self):
        return self.api_root_url + '/oauth/v2/get_request_token'

    def authorize_url(self):
        return self.api_root_url + '/oauth/v2/request_auth'

    def access_token_url(self):
        return self.api_root_url + '/oauth/v2/get_token'

#
#
#
class TwitterOAuthClient(CommonOAuthClient):
    api_root_url = 'http://twitter.com' #for testing 'http://term.ie'
    api_root_port = "80"

    #set api urls
    def request_token_url(self):
        return self.api_root_url + '/oauth/request_token'
    def authorize_url(self):
        #return self.api_root_url + '/oauth/authorize'
        return self.api_root_url + '/oauth/authenticate'
    def access_token_url(self):
        return self.api_root_url + '/oauth/access_token'

#
#
#
class LinkedinOAuthClient(CommonOAuthClient):
    api_root_url = 'https://api.linkedin.com' #for testing 'http://term.ie'
    api_root_port = "443"

    #set api urls
    def request_token_url(self):
        return self.api_root_url + '/uas/oauth/requestToken'
    def authorize_url(self):
        return self.api_root_url + '/uas/oauth/authorize'
    def access_token_url(self):
        return self.api_root_url + '/uas/oauth/accessToken'

    def send_post(self, url, postdata) :
        req = oauth.OAuthRequest.from_consumer_and_token(self.consumer, self.token, 'POST', url, None)
        req.sign_request(self.sha1_method, self.consumer, self.token)

        headers = req.to_header(realm='https://api.linkedin.com')

        logging.debug('OAuth URL : %s' % url)
        logging.debug('OAuth Data : %s' % str(postdata))

        urlinfo = urlsplit(url)

        if urlinfo[0] == 'http' :
            client = httplib.HTTPConnection(urlinfo[1])
        elif urlinfo[0] == 'https' :
            client = httplib.HTTPSConnection(urlinfo[1])

        if 'User-Agent' not in headers :
            headers['User-Agent'] = 'OAuth Python Client Library'

        headers['Content-Length'] = len(postdata)

        client.request('POST', urlinfo[2], postdata, headers)

        response = client.getresponse()

        data = response.read()

        if response.status not in (200, 201) :
            raise Exception("HTTP Status: %d -- message: %s" % (response.status, data))
        client.close()
        return data
#
#
#
if __name__ == '__main__':
    consumer_key = ''
    consumer_secret = ''
    while not consumer_key:
        consumer_key = raw_input('Please enter consumer key: ')
    while not consumer_secret:
        consumer_secret = raw_input('Please enter consumer secret: ')
    auth_client = TwitterOAuthClient(consumer_key,consumer_secret)
    tok = auth_client.get_request_token()
    token = tok['oauth_token']
    token_secret = tok['oauth_token_secret']
    url = auth_client.get_authorize_url(token) 
    webbrowser.open(url)
    print "Visit this URL to authorize your app: " + url
    response_token = raw_input('What is the oauth_token from twitter: ')
    response_client = TwitterOAuthClient(consumer_key, consumer_secret,token, token_secret) 
    tok = response_client.get_access_token()
    print "Making signed request"
    #verify user access
    content = response_client.oauth_request('https://twitter.com/account/verify_credentials.json', method='POST')
    #make an update
    #content = response_client.oauth_request('https://twitter.com/statuses/update.xml', {'status':'Updated from a python oauth client. awesome.'}, method='POST')
    print content
   
    print 'Done.'
