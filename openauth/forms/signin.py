from snippets.forms import FormMixin, MyForm
from ..models import User
from django import forms
import uuid, base64
from profile.models import UserEmail

class SignInUpForm(MyForm, forms.ModelForm) :
    class Meta : 
        model = User
        fields = ['email','password']

    email = forms.EmailField(required=True,
                            widget=forms.TextInput(attrs={'class':''}),
                            help_text="")

    password = forms.CharField(required=True,
                            widget=forms.PasswordInput(attrs={'class':''}),
                            help_text="")

    def clean(self) :
        if 'email' in self.cleaned_data :
            self.user = self.get_user()
            if not self.user and UserEmail.objects.filter(email=self.cleaned_data['email'], is_confirmed=True).exists() :
                raise forms.ValidationError("Unable to match email and password")
        return self.cleaned_data

    def get_user(self) :
        if 'email' in self.cleaned_data and 'password' in self.cleaned_data :
            try :
                uemail = UserEmail.objects.get(email=self.cleaned_data['email'], is_confirmed=True)
                if uemail.user.check_password(self.cleaned_data['password']) :
                    return uemail.user
                return None
            except UserEmail.DoesNotExist :
                pass

            for uemail in UserEmail.objects.filter(email=self.cleaned_data['email'], is_confirmed=False).all() :
                if uemail.user.check_password(self.cleaned_data['password']) :
                    return uemail.user

        return None

class SignInForm(MyForm, forms.ModelForm) :
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

class SignUpForm(MyForm, forms.ModelForm) :
    class Meta : 
        model = User
        fields = ['username','email', 'password']

    username = forms.CharField(required=True,
                            widget=forms.TextInput(attrs={'class':''}),
                            label="User Name",
                            help_text="")

    email = forms.EmailField(required=True,
                            widget=forms.TextInput(attrs={'class':''}),
                            help_text="")

    password = forms.CharField(required=True,
                            widget=forms.PasswordInput(attrs={'class':''}),
                            min_length=8,
                            help_text="")
                            
    terms = forms.BooleanField(required=True, label="")

    def clean_email(self) :
        email = self.cleaned_data['email']

        from profile.models import UserEmail

        if UserEmail.objects.filter(email=email, is_confirmed=True).exists() or User.objects.filter(email=email).exists() :
            raise forms.ValidationError("Email is already registered")

        return email

    def save(self, request) :
        from ..models import create_user

        create_user(request, self.cleaned_data['email'], self.cleaned_data['password'], self.cleaned_data['username'])
