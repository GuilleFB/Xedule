from django import forms

from .models import Tweet
from .models import TwitterCredentials


class TweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ["content", "scheduled_time"]
        widgets = {
            "scheduled_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Excel File",
        help_text="Upload an Excel file (.xlsx) with tweets to schedule",
    )


class TwitterCredentialsForm(forms.ModelForm):
    class Meta:
        model = TwitterCredentials
        fields = ["api_key", "api_secret_key", "access_token", "access_token_secret"]
        widgets = {
            "api_key": forms.TextInput(attrs={"placeholder": "Twitter API Key"}),
            "api_secret_key": forms.TextInput(
                attrs={"placeholder": "Twitter API Secret Key"}
            ),
            "access_token": forms.TextInput(
                attrs={"placeholder": "Twitter Access Token"}
            ),
            "access_token_secret": forms.TextInput(
                attrs={"placeholder": "Twitter Access Token Secret"}
            ),
        }
