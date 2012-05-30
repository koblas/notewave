import settings
import uuid, base64
from snippets.models import JSONField
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User

import oauth.client

GENERATED_USERBASE = '!***!'

OPENID_SERVICES = {
    'google'   : oauth.client.GoogleOAuthClient,
    'yahoo'    : oauth.client.YahooOAuthClient,
    'twitter'  : oauth.client.TwitterOAuthClient,
    'linkedin' : oauth.client.LinkedinOAuthClient,
    #'facebook' : oauth.client.FacebookOAuthClient,
}

def create_user(request, email, password, username=None, is_confirmed=False) :
    import uuid, base64
    from profile.models import UserEmail

    uid  = GENERATED_USERBASE + base64.urlsafe_b64encode(uuid.uuid1().bytes).rstrip('=')

    user = User.objects.create_user(uid, email)
    user.set_password(password)

    user.save()

    useremail = UserEmail(user=user, email=email, is_confirmed=is_confirmed, is_primary=True)
    useremail.key = useremail.gen_key()
    useremail.save()

    if not is_confirmed :
        useremail.send_confirm(request)

    if not username :
        username = email.split('@')[0]
    user.profile.username = username
    user.profile.save()

    return user

#
#  OpenID or Facebook user store
#
class OpenUser(models.Model) :
    """OpenSocial user"""
    class Meta :
        unique_together = (('openid', 'source'),)

    class NoProvider(Exception) : pass

    openid  = models.CharField(max_length=100)
    source  = models.CharField(max_length=10)
    user    = models.ForeignKey(User, db_index=True)
    data    = JSONField(blank=True, null=True)

    def __str__(self) :
        return "<OpenUser %s - %s>" % (self.source, self.openid)

    def get_authinfo(self) :
        p = self.openid.split(':')
        if p[0] == 'facebook' :
            return (p[0], p[1])
        if p[0] == 'fboauth' :
            return (p[0], p[1])
        if p[0] == 'oauth' :
            return (p[1], p[2])
        if p[0] in ('http', 'https') :
            from urlparse import urlsplit

            scheme, netloc, path, query, frag = urlsplit(self.openid)
            if netloc == 'www.google.com' :
               return ('google', None)
            if netloc == 'me.yahoo.com' :
               return ('yahoo', None)
        return (None, None)
        
    def get_service(self) :
        p = self.openid.split(':')
        if p[0] == 'facebook' :
            return p[0]
        if p[0] == 'oauth' :
            return p[1]
        if p[0] in ('http', 'https') :
            from urlparse import urlsplit

            scheme, netloc, path, query, frag = urlsplit(self.openid)
            if netloc == 'www.google.com' :
               return 'google'
            if netloc == 'me.yahoo.com' :
               return 'yahoo'
        return None

    def client(self, site) :
        try :
            oa = OAuthStore.objects.get(user=self.user, source=site)
        except OAuthStore.DoesNotExist :
            return None
        return oa.client()

    @classmethod
    def client_for(cls, site, **kwargs) :
        if site not in OPENID_SERVICES or site not in settings.OPENAUTH_DATA :
            raise cls.NoProvider()
        return OPENID_SERVICES[site](settings.OPENAUTH_DATA[site]['key'], settings.OPENAUTH_DATA[site]['secret'], **kwargs)

class OAuthStoreOpener(object) :
    def __init__(self, client) :    
        self.client = client

    def open(self, url, args = None, method = None) :   
        from StringIO import StringIO
    
        if args and len(args) != 0 and isinstance(args, basestring) :
            nargs = {}
            for arg in args.split('&') :
                (k,v) = arg.split('=',2)
                nargs[k] = v
            args = nargs

        return StringIO(self.client.oauth_request(url, args, method))

class OAuthStore(models.Model) :
    """Store the OAuth tokens we get from different services for a user
    """
    class Meta :
        unique_together = (('user', 'source'),)

    token   = models.CharField(max_length=1024)
    secret  = models.CharField(max_length=1024, null=True)
    expires = models.DateTimeField(null=True, blank=True)

    source  = models.CharField(max_length=100)
    user    = models.ForeignKey(User, db_index=True)

    def get_opener(self, consumer_key, consumer_secret) :
        from oauth.client import CommonOAuthClient

        client = CommonOAuthClient(consumer_key, consumer_secret, self.token, self.secret)

        return OAuthStoreOpener(client)

    def client(self) :
        factory = OPENID_SERVICES[self.source]
        return factory(settings.OPENAUTH_DATA[self.source]['key'],
                       settings.OPENAUTH_DATA[self.source]['secret'],
                       oauth_token=self.token, oauth_token_secret=self.secret)

    def __str__(self) :
        return "<OAuthStore token=%s secret=%d chars>" % (self.token, len(self.secret))

# 
#  OpenID classes
#
class OpenidNonce(models.Model):
    server_url = models.TextField(max_length=2047)
    salt       = models.CharField(max_length=40)
    expires    = models.IntegerField()

    def __str__(self):
        return "Nonce: %s" % self.nonce

class OpenidAssociation(models.Model):
    server_url = models.TextField(max_length=2047)
    handle     = models.CharField(max_length=255)
    secret     = models.TextField(max_length=255) # Stored base64 encoded
    issued     = models.IntegerField()
    lifetime   = models.IntegerField()
    assoc_type = models.TextField(max_length=64)

    def __str__(self):
        return "Association: %s, %s" % (self.server_url, self.handle)

class PasswordRecovery(models.Model) :
    class Meta :
        pass

    user       = models.ForeignKey(User, unique=True)
    rcode      = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create(cls, user) :
        r = cls()
        r.user = user
        r.rcode = base64.urlsafe_b64encode(uuid.uuid1().bytes).rstrip('=')
        return r

#
#  Extend the User Object...
#
def _user_is_confirmed_get(u) :
    if not hasattr(u, '_cached_confirm') :
        u._cached_confirm = (u.openuser_set.count() != 0)
    return u._cached_confirm

User.is_confirmed = property(_user_is_confirmed_get)
