from django.db import models
from django.db.models.signals import post_save, m2m_changed, post_delete
from django.dispatch import Signal
from django.contrib.auth.models import User
from snippets.models import JSONField
     
class UserProfile(models.Model):
    class InsufficientFunds(Exception) :
        pass

    user  = models.ForeignKey(User, unique=True)
    data  = JSONField(blank=True, null=True)
    image = models.ImageField(upload_to="avatars/%Y/%m-%d", blank=True, null=True)
    username = models.CharField(blank=True, null=True, max_length=120)
    activity_at = models.DateTimeField(auto_now=True, auto_now_add=True)

    balance     = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Stat fields
    submission_count = models.IntegerField(null=True, default=0)
    question_count   = models.IntegerField(null=True, default=0)
    gold_count       = models.IntegerField(null=True, default=0)
    silver_count     = models.IntegerField(null=True, default=0)
    bronze_count     = models.IntegerField(null=True, default=0)

    def name(self) :
        if self.username :
            return self.username
        nm = self.user.get_full_name()
        if not nm :
            return 'Unknown[%d]' % self.user.id
        return nm

    def _url(self, w, h) :
        import time
        modtime = int(time.mktime(self.activity_at.timetuple()))
        #return "/profile/icon/%s_%dx%d.png?%d" % (self.user.id, w, h, modtime)
        #return "/image/%s.%s/%s_%dx%d.png?%d" % (self.__class__.__module__, self.__class__.__name__, self.user.id, w, h, modtime)
        import image
        return image.url(self, self.user.id, w, h, modtime)

    def icon(self, size) :
        return self._url(size, size)

    def icon24(self) : 
        return self._url(24, 24)
    def icon25(self) : 
        return self._url(25, 25)
    def icon32(self) : 
        return self._url(32, 32)
    def icon40(self) : 
        return self._url(40, 40)
    def icon50(self) : 
        return self._url(50, 50)
    def icon48(self) : 
        return self._url(48, 48)
    def icon64(self) : 
        return self._url(64, 64)
    def icon96(self) : 
        return self._url(96, 96)
    def icon150(self) : 
        return self._url(150, 150)

    @classmethod
    def icon_image(cls, uid) :
        try :
            profile = cls.objects.get(user=uid)
            return profile.image
        except Exception, e:
            return None
        

    def transact_money(self, amount, ref=None) :
        from django.db.models import F

        if amount < 0 and self.balance + amount < 0 :
            raise self.InsufficientFunds

        trans = UserTransaction(user=self.user, amount=amount, references=ref)
        trans.save()

        self.balance = F('balance') + amount
        self.save()

    def get_absolute_url(self) :
        return "/profile/%s/%s" % (self.user.id, self.name())

    @property
    def email(self) :
        best = None
        for ue in UserEmail.objects.filter(user=self.user, is_confirmed=True) :
            if ue.is_primary :
                return ue.email
            best = ue.email
        return best

    def is_anonymous(self)    : return self.user.is_anonymous()
    def is_authenticated(self): return self.user.is_authenticated()

    def registered_services(self) :
        return [ou.get_service() for ou in self.user.openuser_set.all()]

    def following_count(self) :
        return self.user.follows.count()

    def followers_count(self) :
        return self.user.followed_by.count()

    def notifications(self) :
        return UserNotification.objects.filter(user=self.user, is_read=False)

    def is_confirmed(self) :
        return UserEmail.objects.filter(user=self.user, is_confirmed=True).exists()

    #
    #  Will build a better pattern later...
    #
    def show_new_user(self) :
        return self.data.get('sysmsg',{}).get('new_user', True)

    def set_sysmsg(self, id, value) :
        if not self.data.get('sysmsg', None) :
            self.data['sysmsg'] = {id : value}
        else :
            self.data['sysmsg'][id] = value

    def __str__(self) :
        return '%s Profile' % self.name()

class History(models.Model) :
    user        = models.ForeignKey(User, db_index=True)
    event       = models.CharField(max_length=2, default='en')
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

class Accounting(models.Model) :
    user        = models.ForeignKey(User, db_index=True)
    event       = models.CharField(max_length=2, default='en')
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)

class AnonymousProfile(object) :
    """API Comptatible version of the UserProfie"""

    @property
    def username(self) : return None
    @property
    def email(self) : return None

    def can_vote_up(self)     : return False
    def can_vote_flag(self)   : return False
    def can_vote_down(self)   : return False
    def can_create_tags(self) : return False

    def __unicode__(self)     : return u"AnonymousUser"

    def is_anonymous(self)    : return True
    def is_authenticated(self): return False

class UserEmail(models.Model) :
    class Meta :
        unique_together = (('user','email'),)
        ordering = ('-is_primary','-is_confirmed', 'email')

    user        = models.ForeignKey(User, db_index=True, related_name='following')
    email       = models.EmailField(max_length=120, db_index=True)
    is_primary  = models.BooleanField(default=False)
    is_confirmed= models.BooleanField(default=False)
    key         = models.CharField(max_length=60, null=True, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    def gen_key(self) :
        import hashlib, time, base64
        import settings
        m = hashlib.md5()
        m.update(settings.SECRET_KEY)
        m.update("%r%r" % (self.user.id, time.time()))
        return base64.b32encode(m.digest()).strip('=')[0:10]

    def send_confirm(self, request) :
        from snippets.email import email_template
        from django.core.urlresolvers import reverse
        from django.template import RequestContext

        url = request.build_absolute_uri(reverse('profile:confirm_email', kwargs={'userid':self.user.id, 'key':self.key}))

        email_template(subject = 'Notewave | Please confirm your email address',
                       rcpt = [self.email],
                       sender = 'help@notewave.com',
                       text = 'profile/_email_confirm.txt',
                       html = 'profile/_email_confirm.html',
                       context_instance = RequestContext(request, {
                            'addr'   : self.email,
                            'name'   : self.user.profile.name(),
                            'url'    : url,
                        }))

class UserFollow(models.Model) :
    class Meta :
        unique_together = (('user','following'),)

    user        = models.ForeignKey(User, db_index=True, related_name='follows')
    following   = models.ForeignKey(User, db_index=True, related_name='followed_by')
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

class UserTransaction(models.Model) :
    user        = models.ForeignKey(User, db_index=True, related_name='transactions')
    amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    references  = JSONField(blank=True, null=True)

#
#
#
class UserNotification(models.Model) :
    class Meta :
        ordering = ['-created_at']

    KIND_FOLLOW     = 0
    KIND_SUBMISSION = 1
    KIND_FUND       = 2
    KIND_COMMENT_Q  = 3
    KIND_COMMENT_R  = 4
    KIND_CREATE     = 5
    
    KIND_CHOICES = (
        (KIND_FOLLOW,     'Follow'),
        (KIND_FUND,       'Fund'),
        (KIND_SUBMISSION, 'Submission'),
        (KIND_COMMENT_Q,  'Question Comment'),
        (KIND_COMMENT_R,  'Research Comment'),
    )

    user        = models.ForeignKey(User, db_index=True)
    kind        = models.SmallIntegerField(null=True, choices=KIND_CHOICES)
    data        = JSONField(blank=True, null=True)
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    def __init__(self, *args, **kwargs) :
        super(UserNotification, self).__init__(*args, **kwargs)

        self.__by_user  = None
        self.__question = None
        self.__research = None

    @classmethod
    def send_create(cls, user, question) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_CREATE, data={ 'user_id' : question.user.id, 'question': question.guid })
            obj.save()

    @classmethod
    def send_follow(cls, user, by_user) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_FOLLOW, data={ 'user_id': by_user.id })
            obj.save()

    @classmethod
    def send_comment_research(cls, user, research, by_user) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_COMMENT_R, data={ 
                        'question' : research.question.guid, 
                        'research': research.guid, 
                        'user_id' : by_user.id 
                    })
            obj.save()

    @classmethod
    def send_comment_question(cls, user, question, by_user) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_COMMENT_Q, data={ 'question': question.guid, 'user_id' : by_user.id })
            obj.save()

    @classmethod
    def send_comment_research(cls, user, research, by_user) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_COMMENT_R, data={ 'research': research.guid, 'user_id' : by_user.id })
            obj.save()

    @classmethod
    def send_fund(cls, user, question, amount, by_user) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_FUND, data={ 
                                            'question': question.guid, 
                                            'amount' : amount, 
                                            'user_id' : by_user.id 
                                    })
            obj.save()

    @classmethod
    def send_submission(cls, user, research, by_user, is_update) :
        if not hasattr(user, '__iter__') :
            user = [user]
        for u in user :
            obj = cls(user=u, kind=cls.KIND_SUBMISSION, data={ 
                                            'question' : research.question.guid,  
                                            'research': research.guid, 
                                            'user_id' : by_user.id,
                                            'update'  : is_update,
                                    })
            obj.save()

    def _by_user(self) :
        if self.__by_user is None and 'user_id' in self.data :
            self.__by_user = User.objects.get(id=self.data['user_id'])
        return self.__by_user
    by_user = property(_by_user)

    def _question(self) :
        from crowd.models import Document
        if self.__question is None and 'question' in self.data :
            self.__question = Document.byguid(self.data['question'])
        return self.__question
    question = property(_question)

    def _research(self) :
        from crowd.models import Document
        if self.__research is None and 'research' in self.data :
            self.__research = Document.byguid(self.data['research'])
        return self.__research
    research = property(_research)




#
#  Extend the User Object...
#
def _user_profile_get(u) :
    if not hasattr(u, '_cached_profile') :
        u._cached_profile = UserProfile.objects.get_or_create(user=u)[0]
    return u._cached_profile

def _user_is_email_confirmed_get(u) :
    if not hasattr(u, '_cached_confirm') :
        u._cached_email_confirm = UserEmail.objects.filter(user=u, is_confirmed=True).exists()
    return u._cached_email_confirm

User.is_email_confirmed = property(_user_is_email_confirmed_get)
User.profile = property(_user_profile_get)
