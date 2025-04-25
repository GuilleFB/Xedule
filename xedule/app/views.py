# tweets/views.py
from io import BytesIO

import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.edit import FormView

from .forms import ExcelUploadForm
from .forms import TweetForm
from .models import Tweet
from .utils import process_excel_file

EXCEPTION = "You do not have permission to modify/delete this tweet"
LENGTH_ERROR_MESSAGE = 10


class UserOwnsTweetMixin:
    def dispatch(self, request, *args, **kwargs):
        tweet = self.get_object()
        if tweet.user != request.user:
            raise PermissionDenied(EXCEPTION)
        return super().dispatch(request, *args, **kwargs)


class TweetListView(LoginRequiredMixin, ListView):
    model = Tweet
    template_name = "app/tweet_list.html"
    context_object_name = "tweets"
    paginate_by = 10

    def get_queryset(self):
        return Tweet.objects.filter(user=self.request.user).order_by("-created_at")


class TweetDetailView(LoginRequiredMixin, DetailView):
    model = Tweet
    template_name = "app/tweet_detail.html"
    context_object_name = "tweet"


class TweetCreateView(LoginRequiredMixin, CreateView):
    model = Tweet
    form_class = TweetForm
    template_name = "app/tweet_form.html"
    success_url = reverse_lazy("tweet_list")

    def form_valid(self, form):
        form.instance.user = self.request.user  # Asigna el usuario actual al tweet
        return super().form_valid(form)


class TweetUpdateView(LoginRequiredMixin, UserOwnsTweetMixin, UpdateView):
    model = Tweet
    form_class = TweetForm
    template_name = "app/tweet_form.html"
    success_url = reverse_lazy("tweet_list")

    def get_queryset(self):
        # Solo permite editar tweets del usuario actual
        return super().get_queryset().filter(user=self.request.user)


class TweetDeleteView(LoginRequiredMixin, UserOwnsTweetMixin, DeleteView):
    model = Tweet
    template_name = "app/tweet_confirm_delete.html"
    success_url = reverse_lazy("tweet_list")

    def get_queryset(self):
        # Solo permite borrar tweets del usuario actual
        return super().get_queryset().filter(user=self.request.user)


class TweetBulkUploadView(LoginRequiredMixin, FormView):
    form_class = ExcelUploadForm
    template_name = "app/tweet_bulk_upload.html"
    success_url = reverse_lazy("tweet_list")

    def form_valid(self, form):
        excel_file = self.request.FILES["excel_file"]

        # Check file extension
        if not excel_file.name.endswith(".xlsx"):
            messages.error(self.request, "Please upload an Excel file (.xlsx)")
            return self.form_invalid(form)

        # Process the Excel file
        result = process_excel_file(excel_file, self.request.user)

        if result["success"]:
            messages.success(
                self.request,
                f"Successfully created {result['tweets_created']} tweets. "
                f"Failed: {result['tweets_failed']}.",
            )

            # If there are error messages, show them
            if result["error_messages"]:
                error_list = "<br>".join(
                    result["error_messages"][:LENGTH_ERROR_MESSAGE]
                )
                if len(result["error_messages"]) > LENGTH_ERROR_MESSAGE:
                    error_list += "<br>...and more."
                messages.warning(
                    self.request, f"Errors: {error_list}", extra_tags="safe"
                )
        else:
            messages.error(self.request, f"Error: {result['message']}")
            return self.form_invalid(form)

        return super().form_valid(form)


class DownloadTemplateView(View):
    def get(self, request, *args, **kwargs):
        # Create a sample dataframe with the expected structure
        tweet_template_df = pd.DataFrame(
            {
                "content": [
                    "This is a sample tweet content. Replace with your actual tweet.",
                    "Another example tweet. You can add as many rows as needed.",
                ],
                "scheduled_time": [
                    pd.Timestamp("2025-05-01 10:00:00"),
                    pd.Timestamp("2025-05-02 15:30:00"),
                ],
            }
        )

        # Create a BytesIO object to save the Excel file
        buffer = BytesIO()

        # Create the Excel writer using the BytesIO object as the file
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            tweet_template_df.to_excel(writer, index=False, sheet_name="Tweets")

            # Auto-adjust columns' width
            worksheet = writer.sheets["Tweets"]
            for i, col in enumerate(tweet_template_df.columns):
                max_length = max(
                    tweet_template_df[col].astype(str).map(len).max(), len(col)
                )
                # Adding a little extra space
                worksheet.column_dimensions[chr(65 + i)].width = max_length + 2

        # Set up the response
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            "attachment; filename=tweet_upload_template.xlsx"
        )

        return response
