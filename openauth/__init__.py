from datetime import datetime, timedelta
from django.core.exceptions import ImproperlyConfigured
from hashlib import md5
import settings

AUTH_COOKIE = 'zqauth'
try :
    AUTH_DOMAIN = settings.AUTH_DOMAIN
except :
    AUTH_DOMAIN = None

def load_backend(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = __import__(module, {}, {}, [attr])
    except ImportError, e:
        raise ImproperlyConfigured, 'Error importing authentication backend %s: "%s"' % (module, e)
    except ValueError, e:
        raise ImproperlyConfigured, 'Error importing authentication backends. Is AUTHENTICATION_BACKENDS a correctly defined list or tuple?'
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured, 'Module "%s" does not define a "%s" authentication backend' % (module, attr)
    return cls()

def get_backends():
    from django.conf import settings
    backends = []
    for backend_path in settings.AUTHENTICATION_BACKENDS:
        backends.append(load_backend(backend_path))
    return backends

def authenticate(**credentials):
    """
    If the given credentials are valid, return a User object.
    """
    for backend in get_backends():
        try:
            user = backend.authenticate(**credentials)
        except TypeError:
            # This backend doesn't accept these credentials as arguments. Try the next one.
            continue
        if user is None:
            continue
        # Annotate the user object with the path of the backend.
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        return user

def login(request, user, remember=True) :
    """
    Persist a user id and a backend in the request. This way a user doesn't
    have to reauthenticate on every request.
    """
    if user is None:
        user = request.user

    user.last_login = datetime.now()
    user.save()

    ts = str(user.last_login)
    k = "|".join([
                    str(user.id), 
                    ts, 
                    user.backend, 
                    md5("|".join([str(user.id), ts, user.backend, settings.SECRET_KEY])).hexdigest()
                ])

    if remember :
        expires = datetime.now() + timedelta(days=366)
        request._authMiddleware.set_cookie(cookie=AUTH_COOKIE, value=k, expires=expires)
    else :
        request._authMiddleware.set_cookie(cookie=AUTH_COOKIE, value=k)

    if hasattr(request, 'user'):
        request.user = user

def logout(request):
    """
    Removes the authenticated user's ID from the request and flushes their
    session data.
    """
    if hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    if 'facebook' in settings.OPENAUTH_DATA :
        key = settings.OPENAUTH_DATA['facebook']['key']
        if key in request.COOKIES :
            request._authMiddleware.delete_cookie(cookie=key)
            key = key + '_'
            for k in request.COOKIES.keys() :
                if k.startswith(key) :
                    request._authMiddleware.delete_cookie(cookie=k)

    request._authMiddleware.delete_cookie(cookie=AUTH_COOKIE)

def get_user(request):
    from django.contrib.auth.models import AnonymousUser

    if 'facebook' in settings.OPENAUTH_DATA :
        from facebook import Facebook
        fb = Facebook(settings.OPENAUTH_DATA['facebook']['key'], settings.OPENAUTH_DATA['facebook']['secret'])
        fb.check_session(request)
        if fb.uid is not None :
            identity = 'facebook:%s' % fb.uid
            try :
                from .models import OpenUser
                oiuser = OpenUser.objects.get(openid=identity, source='openid')
                return oiuser.user
            except OpenUser.DoesNotExist :
                pass

    try:
        auth = request.COOKIES.get(AUTH_COOKIE, '')

        parts = auth.split('|')
        if len(parts) != 4 :
            user = AnonymousUser()
        elif parts[3] == md5("|".join([parts[0], parts[1], parts[2], settings.SECRET_KEY])).hexdigest() :
            backend = load_backend(parts[2])
            user    = backend.get_user(parts[0]) or AnonymousUser()
        else :
            user = AnonymousUser()
    except KeyError:
        user = AnonymousUser()
    return user

def context_processor(request) :
    key = None
    if 'facebook' in settings.OPENAUTH_DATA and 'key' in settings.OPENAUTH_DATA['facebook'] :
        key = settings.OPENAUTH_DATA['facebook']['key']

    result = {}

    user = get_user(request)
    if not user.is_anonymous() :
        from views import GENERATED_USERBASE
        result.update({
            'openauth' : {
                'need_name'   : len(user.get_full_name()) == 0,
                #'need_screen' : user.username.find(GENERATED_USERBASE) == 0,
                'need_email'  : user.email == '',
            }
        })

    inCanvas = False
    if 'facebook' in settings.OPENAUTH_DATA :
        from facebook import Facebook
        fb = Facebook(settings.OPENAUTH_DATA['facebook']['key'], settings.OPENAUTH_DATA['facebook']['secret'])
        fb.check_session(request)
        inCanvas = fb.in_canvas

    result.update({
                'facebook' : {
                    'apikey' : key,
                    'inCanvas' : inCanvas,
                }
            })

    return result
