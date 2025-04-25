from django import forms

from .models import Tweet


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
