from snippets.forms import MyForm, FormMixin
from ..models import User
from django import forms
import uuid, base64
#from profile.models import UserEmail

class InviteGroupForm(MyForm, forms.Form) :
    email = forms.EmailField(required=True,
                            help_text="")

