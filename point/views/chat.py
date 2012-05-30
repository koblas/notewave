from django.template import RequestContext
#from django.shortcuts import render_to_response
#from django.http import HttpResponse
#import json
#import time 
#import tornado.web
#from django_tornado.decorator import asynchronous
from datetime import datetime
from snippets.async import AsyncResponse

AVAIL = {}

def avail(request) :
    async = AsyncResponse(request)
    if request.user.is_anonymous() :
        return async.message("not logged in")
    AVAIL[request.user.id] = datetime.now()
    return async

def depart(request) :
    async = AsyncResponse(request)
    if request.user.is_anonymous() :
        return async.message("not logged in")
    if request.user.id in AVAIL :
        del AVAIL[request.user.id]
    return async
