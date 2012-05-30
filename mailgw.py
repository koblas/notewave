#!/usr/bin/python

import sys

rcpt = sys.argv[2]
body = sys.stdin.read()

if rcpt in ('koblas', 'help', 'robot') :
    import smtplib

    s = smtplib.SMTP('localhost')
    s.sendmail('robot@notewave.com', ['koblas@extra.com'], body)
    s.quit()

else :
    import urllib2, urllib

    url = 'http://dev.notewave.com/email'
    values = { 'rcpt' : rcpt, 'body' : body }
    headers = { 'User-Agent' : 'emtest', 'Host' : 'notewave.com' }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data, headers)
    try :
        response = urllib2.urlopen(req)
    except urllib2.HTTPError, e :
        print e.read()
        sys.exit(1)
    else :
        v = response.read()
        if v[0] != '+' :
            print v
            sys.exit(1)
