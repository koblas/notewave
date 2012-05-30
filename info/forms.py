import re, json, copy
from django import forms
from . import MyForm
from .form_mixin import FormMixin
from ..models import Comment, Question, Tag, Funder, Worker, QuestionTag, Research, ResearchFile

class SupportForm(MyForm, forms.Form) :
    subject = forms.CharField(required=False, 
                            widget=forms.TextInput(attrs={'class':''}), 
                            help_text="use tags to add more information about your question")

    body       = forms.CharField(required=False, 
                            widget=forms.Textarea(attrs={'class':'rte'}), 
                            help_text="Message To Send")
