from snippets.forms import MyForm, FormMixin
from ..models import User
from django import forms
import uuid, base64
#from profile.models import UserEmail

class SignInForm(MyForm, forms.Form) :
    class Meta : 
        model = User
        fields = ['email','password']

    email = forms.EmailField(required=False,
                            widget=forms.TextInput(attrs={'class':''}),
                            help_text="")

    password = forms.CharField(required=False,
                            widget=forms.PasswordInput(attrs={'class':''}),
                            help_text="")

    def clean(self) :
        if 'email' in self.cleaned_data :
            user = self.get_user()
            if not user :
                raise forms.ValidationError("Unable to match email and password")
        return self.cleaned_data

    def get_user(self) :
        user = None
        if 'email' in self.cleaned_data :
            for uemail in UserEmail.objects.filter(email=self.cleaned_data['email']).all() :
                if uemail.user.check_password(self.cleaned_data['password']) :
                    if uemail.is_confirmed :
                        user = uemail.user
                    elif user is None :
                        user = uemail.user

        return user
