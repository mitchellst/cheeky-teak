from django import forms

class UploadFileForm(forms.Form):
    event = forms.IntegerField()
    csvfile = forms.FileField()
