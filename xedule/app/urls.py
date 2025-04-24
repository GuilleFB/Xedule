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
]
