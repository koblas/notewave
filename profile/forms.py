from django import forms
from snippets.forms import MyForm

class ProfileAboutForm(MyForm, forms.Form) :
    username  = forms.CharField(required=False, 
                            widget=forms.TextInput(attrs={'class':''}), 
                            help_text="How people know you on the service")

    #bio  = forms.CharField(required=False, 
    #                        widget=forms.Textarea(attrs={'class':'rte'}), 
    #                        help_text="How people know you on the service")

class ProfileSignupForm(MyForm, forms.Form) :
    bio  = forms.CharField(required=False, 
                            widget=forms.Textarea(attrs={'class':'rte'}), 
                            label="Your Bio",
                            help_text="How people know you on the service", initial="""
                            <p><em>Please describe yourself</em>
                            <br/><em>Expertise</em>
                            <br/><em>Career highlights</em>
                            <br/><em>Interests</em>
                            </p>
                            """)

class ProfilePhotoForm(MyForm, forms.Form) :
    photo = forms.ImageField(required=True)

class ProfileEmailAddrForm(MyForm, forms.Form) :
    email  = forms.EmailField(required=False, 
                              help_text="")

class PasswordForm(MyForm, forms.Form) :
    password  = forms.CharField(required=True, 
                            widget=forms.PasswordInput(attrs={'class':''}), 
                            min_length=8,
                            help_text="")

    password2 = forms.CharField(required=True, 
                            widget=forms.PasswordInput(attrs={'class':''}), 
                            label="Password Again",
                            min_length=8,
                            help_text="Just to make sure")

    def clean(self) :
        if 'password' not in self.cleaned_data :
            return self.cleaned_data

        if 'password2' in self.cleaned_data :
            if self.cleaned_data['password'] != self.cleaned_data['password2'] :
                raise forms.ValidationError("Passwords don't match")
            
        return self.cleaned_data


#
# Staff form 
#
class FundForm(MyForm, forms.Form) :
    amount = forms.DecimalField(required=True, 
                            widget=forms.TextInput(attrs={'class':''}), 
                            help_text="")
