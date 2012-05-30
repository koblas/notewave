import settings

try :
    DEFAULT_DOMAIN = settings.AUTH_DOMAIN
except :
    DEFAULT_DOMAIN = None

class LazyUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user') :
            from . import get_user
            request._cached_user = get_user(request)
        return request._cached_user

class AuthenticationMiddleware(object):
    def __init__(self) :
        self._setcookie = []

    def process_request(self, request):
        self._setcookie = []
        request.__class__.user = LazyUser()
        request._authMiddleware = self

        import settings
        if 'facebook' in settings.OPENAUTH_DATA :
            from facebook import Facebook
            fb = Facebook(settings.OPENAUTH_DATA['facebook']['key'], settings.OPENAUTH_DATA['facebook']['secret'])
            fb.check_session(request)

            request.facebook = fb
        else :
            request.facebook = None

        return None

    def process_response(self, request, response):
        for setc in self._setcookie :
            exp    = None
            domain = None

            if 'expires' in setc and setc['expires'] is not None :
                exp = setc['expires'].strftime('%a, %d %b %Y %H:%M:%S')

            if 'domain' in setc and setc['domain'] is not None :
                domain = setc['domain']
            else :
                domain = DEFAULT_DOMAIN

            if setc['value'] is None :
                response.delete_cookie(setc['cookie'], domain=domain)
            else :
                response.set_cookie(setc['cookie'], setc['value'], expires=exp, domain=domain)
            self._setcookie = None

        return response

    def set_cookie(self, cookie=None, value=None, expires=None, domain=None) :
        self._setcookie.append({'cookie':cookie,'value':value,'expires':expires,'domain':domain})

    def delete_cookie(self, cookie=None, domain=None) :
        self._setcookie.append({'cookie':cookie,'value':None,'expires':None,'domain':domain})
