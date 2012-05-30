from django.db import models
from openauth.models import User
from snippets.models import JSONField
import re

# from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
LINK_RE = re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?]))', re.U)
class Group(models.Model) :
    title       = models.CharField(max_length=200, help_text='Group Title')
    created_at  = models.DateTimeField(auto_now_add=True)
    activity_at = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, db_index=True)
    invite_id   = models.CharField(max_length=200, db_index=True)
    eaddr       = models.CharField(max_length=100, db_index=True, null=True, blank=True)

    RESERVED_EMAIL = ('koblas','support','robot','help','service')

    # class variable
    _callbacks  = {}

    def root_post_set(self) :
        return Post.objects.filter(group=self, parent=None)

    def share_url(self) :
        from django.core.urlresolvers import reverse

        return reverse('point:accepturl', args=[self.invite_id])

    def email(self) :
        if not self.eaddr :
            return None
        return '%s@notewave.com' % (self.eaddr)

    def save(self) :
        if not self.invite_id :
            import uuid
            self.invite_id = uuid.uuid1()

        if not self.created_at :
            from django.template.defaultfilters import slugify

            base = potential = slugify(self.title)
            suffix = 0
            while not self.eaddr :
                if potential not in self.RESERVED_EMAIL and not self.__class__.objects.filter(eaddr = potential).exists() :
                    self.eaddr = potential
                else :
                    suffix += 1
                    potential = "%s-%d" % (base, suffix)

        super(Group, self).save()

    def post_update(self, post) :
        from datetime import datetime

        self.activity_at = datetime.now()
        self.save()

        if self.id in self._callbacks :
            for cb in self._callbacks[self.id] :
                cb(self, post)
            self._callbacks[self.id] = []

    def cb_register(self, func) :
        if self.id not in self._callbacks :
            self._callbacks[self.id] = []
        self._callbacks[self.id].append(func)

    def add_member(self, user) :
        # TODO - notify that a member joined
        post = Post(group=self, user=user, body={'join':1})
        post.save()

        member = Member(group=self, user=user)
        member.save()

        return member

class Invite(models.Model) :
    class Meta :
        unique_together = (('user','group','email'),)

    user        = models.ForeignKey(User, db_index=True)
    group       = models.ForeignKey(Group, db_index=True)
    email       = models.CharField(max_length=200, db_index=True)
    guid        = models.CharField(max_length=200, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)

    def save(self) :
        import uuid
        if not self.guid :
            self.guid = uuid.uuid1()
        super(Invite, self).save()

class Member(models.Model) :
    class Meta :
        unique_together = (('user','group'),)

    user        = models.ForeignKey(User, db_index=True)
    group       = models.ForeignKey(Group, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    activity_at = models.DateTimeField(auto_now_add=True)
    lastread_at = models.DateTimeField(auto_now_add=True)
    active      = models.BooleanField(default=True)

    notify_on_post = models.BooleanField(default=True)

    username    = models.CharField(max_length=200, help_text='')
    image       = models.ImageField(upload_to="avatars/%Y/%m-%d", blank=True, null=True)

    def get_username(self) :
        if self.username :
            return self.username
        return self.user.profile.username

    def icon24(self) :
        return self.user.profile.icon(24)

    def icon50(self) :
        return self.user.profile.icon(50)

    def new_count(self) :
        cnt = Post.objects.filter(group=self.group, parent=None, created_at__gt=self.lastread_at).count()
        ccnt = Post.objects.filter(group=self.group, created_at__gt=self.lastread_at).exclude(parent=None).count()

        if cnt == 0 and ccnt == 0 :
            return ""
        if ccnt == 0 :
            return "%d" % cnt
        return "%d/%d" % (cnt, ccnt)

    def _url(self, w, h) :
        import time
        modtime = int(time.mktime(self.activity_at.timetuple()))
        return "/image/%s/%s_%dx%d.png?%d" % (self.__class__.__name__, self.user.id, w, h, modtime)

class Inbox(models.Model) :
    TYPE_INBOX  = 0
    TYPE_SYSTEM = 1

    TYPE_CHOICES = (
                        (TYPE_INBOX,      'Inbox'),
                        (TYPE_SYSTEM,     'System'),
                )

    body        = JSONField(blank=True, null=True)
    user        = models.ForeignKey(User, db_index=True, related_name='message_user')
    sender      = models.ForeignKey(User, db_index=True, related_name='message_sender')
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read     = models.BooleanField(default=False)
    msgtype     = models.IntegerField(default=TYPE_INBOX, choices=TYPE_CHOICES)

class Post(models.Model) :
    class Meta :
        ordering = (('-created_at'),)

    body        = JSONField(blank=True, null=True)
    user        = models.ForeignKey(User, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    parent      = models.ForeignKey('self', null=True, blank=True, default=None)
    group       = models.ForeignKey(Group, db_index=True)
    likes       = models.IntegerField(default=0)

    def links(self) :
        if not hasattr(self, '_links') :
            if 'text' in self.body :
                self._links = [link[0] for link in LINK_RE.findall(self.body['text'])]
            else :
                self._links = []
        return self._links

    def links_youtube(self) :
        res = []
        for link in self.links() :
            id = self._is_youtube(link)
            if id :
                res.append(id)
        return res

    @staticmethod
    def _is_youtube(link) :
        exp = re.compile(r'youtube\.com/.*\bv=(\w+)')
        r = exp.search(link) 
        if r :
            return r.group(1)
        return None

    @classmethod
    def _replace_html(cls, m) :
        link = m.group(0)
        if cls._is_youtube(link) :
            return ""
        return u'<a href="%s">%s</a>' % (link, link)

    def html(self) :
        from django.utils.safestring import mark_safe
        if 'join' in self.body :
            html = "Joined the group"
        elif 'text' in self.body :
            html = LINK_RE.sub(self._replace_html, self.body['text'])
        else :
            html = ''
        return mark_safe(html)

    def add_image(self, image_bytes) :
        from django.core.files.uploadedfile import InMemoryUploadedFile

        name = 'img_%s_%s_%s.jpg' % (self.user.id, self.group.id, self.id)

        ofd = PostImage.safesize(image_bytes)
        if ofd == None :
            return None

        ipost = PostImage(user=self.user, post=self)
        ipost.image.save(name, InMemoryUploadedFile(ofd, None, name, 'image/jpeg', len(ofd.getvalue()), None), save=False)
        ipost.save()

        self.body['image_count'] = self.body.get('image_count', 0) + 1

        if not hasattr(self, '_images') :
            self._images = []
        self._images.append(ipost)
        return ipost

    def images(self) :
        if self.body.get('image_count', 0) == 0 :
            return None
        if not hasattr(self, '_images') :
            self._images = [img for img in self.postimage_set.all()]
        return self._images

    def member(self) :
        return Member.objects.get(user=self.user, group=self.group)

    def comments(self) :
        return Post.objects.filter(parent=self).order_by('created_at')

    def email_notify(self, request, member, users) :
        from snippets.email import email_template

        from django.core.urlresolvers import reverse
        from django.template import RequestContext

        url = request.build_absolute_uri(reverse('point:readpost', kwargs={'gid':self.group.id, 'pid':self.id}))

        if self.parent is None :
            subject = 'Notewave | New post by: %s' % member.get_username()
        else :
            subject = 'Notewave | Comment by: %s' % member.get_username()

        email_template(subject = subject,
                       rcpt = [user.profile.email for user in users if user.profile.email is not None],
                       sender = 'notify@notewave.com',
                       text = 'point/_email_newpost.txt',
                       html = 'point/_email_newpost.html',
                       context_instance = RequestContext(request, {
                            'member' : member,
                            'post'   : self,
                            'url'    : url,
                        }))

    def share(self, users) :
        pass

    def save(self, notify=True) :
        """ TODO - change to signal based """
        existing = False
        if self.id :
            existing = True
        super(Post, self).save()

        if notify and not existing :
            self.notify()

    def notify(self) :
        self.group.post_update(self)

    def watchers(self, exclude_user=None) :
        users = []
        if self.parent is not None :
            #
            #  Get everybody watching the post
            #
            for obj in Like.objects.filter(post=self).all() :
                if obj.user == self.user :
                    continue
                if exclude_user and exclude_user == obj.user :
                    continue
                users.append(obj.user)

            for obj in Post.objects.filter(parent=self).all() :
                if obj.user == self.user :
                    continue
                if exclude_user and exclude_user == obj.user :
                    continue
                users.append(obj.user)

            if self.parent.user not in users and exclude_user != self.parent.user :
                users.append(self.parent.user)
        else :
            #
            #  Get the member list of the group, excluding the poster and anybody who doesn't follow...
            #
            for m in self.group.member_set.all() :
                if not m.notify_on_post :
                    continue
                if m.user == self.user :
                    continue
                if exclude_user and exclude_user == m.user :
                    continue
                users.append(m.user)
        return users
        
class PostImage(models.Model) :
    user        = models.ForeignKey(User, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    post        = models.ForeignKey(Post, db_index=True)
    image       = models.ImageField(upload_to="post/%Y/%m-%d", blank=True, null=True)

    def _url(self, w, h) :
        import image
        return image.url(self, self.id, w, h)

    def icon100(self) :
        return self._url(100,100)

    def icon130(self) :
        return self._url(130,130)

    @classmethod
    def icon_image(cls, iid) :
        try :
            image = cls.objects.get(id=iid)
            return image.image
        except Exception, e:
            return None

    @staticmethod
    def safesize(bytes) :
        from cStringIO import StringIO
        from PIL import Image

        try :
            img = Image.open(StringIO(bytes))
        except :
            return None
        w, h = img.size

        if w > 640 or h > 640 :
            if w > h :
                scale = 640.0 / w
            else :
                scale = 640.0 / h
            img = img.resize((int(w * scale), int(h * scale)))

        ofd = StringIO()
        img.save(ofd, 'JPEG')
        ofd.seek(0)

        return ofd

class Like(models.Model) :
    class Meta :
        unique_together = (('user','post'),)

    user        = models.ForeignKey(User, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    post        = models.ForeignKey(Post, db_index=True)
