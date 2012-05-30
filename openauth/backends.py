from .models import User

class TokenBackend :
    def authenticate(self, user=None, token=None) :
        return user

    def get_user(self, user_id) :
        try :
            return User.objects.get(pk=user_id)
        except User.DoesNotExist :
            return None
