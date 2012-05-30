
def url(obj, id, width=64, height=64, modtime=None) :
    if modtime :
        return "/image/%s.%s/%s_%dx%d.png?%d" % (obj.__class__.__module__, obj.__class__.__name__, id, width, height, modtime)
    return "/image/%s.%s/%s_%dx%d.png" % (obj.__class__.__module__, obj.__class__.__name__, id, width, height)
