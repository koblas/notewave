
from django.template import RequestContext
from django.shortcuts import render_to_response

def home(request, force=False) :
        return render_to_response('door/home.html', {
                                        }, context_instance=RequestContext(request))
