from snippets.forms import FormMixin, MyForm
from django import forms

class RecoveryForm(MyForm, forms.Form) :
    password = forms.CharField(required=True,
                            widget=forms.PasswordInput(attrs={'class':''}),
                            help_text="")
