from snippets.forms import MyForm, FormMixin
from ..models import User
from django import forms
import uuid, base64
#from profile.models import UserEmail

class EditNameForm(MyForm, forms.Form) :
    name = forms.CharField(required=True,
                            help_text="")

