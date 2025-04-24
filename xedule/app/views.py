# tweets/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .forms import TweetForm
from .models import Tweet

EXCEPTION = "You do not have permission to modify/delete this tweet"


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
