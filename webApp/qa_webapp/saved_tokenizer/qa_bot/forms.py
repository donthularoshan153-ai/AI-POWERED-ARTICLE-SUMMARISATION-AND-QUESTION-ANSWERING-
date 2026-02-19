from django import forms

class InputForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, required=False)
    link = forms.URLField(required=False)
    pdf = forms.FileField(required=False)