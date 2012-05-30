from openid.store.interface import OpenIDStore
from openid.association import Association as OIDAssociation
from openid.yadis import xri

import time, base64
from hashlib import md5

import settings
from models import OpenidAssociation, OpenidNonce

class OpenID:
    def __init__(self, openid, issued, attrs=None, sreg=None) :
        self.openid = openid
        self.issued = issued
        self.attrs = attrs or {}
        self.sreg = sreg or {}
        self.is_iname = (xri.identifierScheme(openid) == 'XRI')

    def __repr__(self):
        return '<OpenID: %s>' % self.openid

    def __str__(self):
        return self.openid

class OpenIDStore(OpenIDStore):
    def __init__(self):
        self.max_nonce_age = 6 * 60 * 60 # Six hours

    def storeAssociation(self, server_url, association):
        assoc = OpenidAssociation(
            server_url = server_url,
            handle     = association.handle,
            secret     = base64.encodestring(association.secret),
            issued     = association.issued,
            lifetime   = association.issued,
            assoc_type = association.assoc_type
        )
        assoc.save()

    def getAssociation(self, server_url, handle=None):
        print "IN getAssociation()"
        assocs = []
        if handle is not None:
            assocs = OpenidAssociation.objects.filter(
                server_url = server_url, handle = handle
            )
        else:
            assocs = OpenidAssociation.objects.filter(
                server_url = server_url
            )
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, base64.decodestring(assoc.secret), assoc.issued,
                assoc.lifetime, assoc.assoc_type
            )
            if association.getExpiresIn() == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]

    def removeAssociation(self, server_url, handle):
        assocs = list(OpenidAssociation.objects.filter(
            server_url = server_url, handle = handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist

    #def storeNonce(self, nonce):
    #    nonce, created = OpenidNonce.objects.get_or_create(
    #        nonce = nonce, defaults={'expires': int(time.time())}
    #    )

    def useNonce(self, server_url, timestamp, salt):
        nonce, created = OpenidNonce.objects.get_or_create(server_url = server_url, salt = salt, defaults={'expires':timestamp})

        if created :    
            return True

        # Now check nonce has not expired
        nonce_age = int(time.time()) - nonce.expires
        if nonce_age > self.max_nonce_age :
            nonce.expires = timestamp
            nonce.save()
            return True
        return False

    def getAuthKey(self):
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        return md5(settings.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]

    def cleanupNonce(self):
            Nonce.objects.filter(timestamp<int(time.time()) - nonce.SKEW).delete()

    def cleanupAssociations(self):
        Association.objects.extra(where=['issued + lifetimeint<(%s)' % time.time()]).delete()

    def isDumb(self):
        return False


def from_openid_response(openid_response):
    issued = int(time.time())
    return OpenID(
        openid_response.identity_url, issued, openid_response.signed_args,
        openid_response.extensionResponse('sreg')
    )
