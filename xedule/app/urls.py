# tweets/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("", views.TweetListView.as_view(), name="tweet_list"),
    path("tweet/<int:pk>/", views.TweetDetailView.as_view(), name="tweet_detail"),
    path("tweet/new/", views.TweetCreateView.as_view(), name="tweet_create"),
    path("tweet/<int:pk>/edit/", views.TweetUpdateView.as_view(), name="tweet_update"),
    path(
        "tweet/<int:pk>/delete/",
        views.TweetDeleteView.as_view(),
        name="tweet_delete",
    ),
    # En app/urls.py, añade esta nueva URL:
    path(
        "tweets/bulk-delete/",
        views.BulkDeleteTweetsView.as_view(),
        name="bulk_delete_tweets",
    ),
    path(
        "tweet/bulk-upload/",
        views.TweetBulkUploadView.as_view(),
        name="tweet_bulk_upload",
    ),
    path(
        "tweet/download-template/",
        views.DownloadTemplateView.as_view(),
        name="download_template",
    ),
]
