from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Tweet(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("published", "Published"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tweets",
        verbose_name="Usuario",
    )

    content = models.TextField(max_length=280, verbose_name="Contenido")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="State",
    )
    scheduled_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Scheduled date and time",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date of creation",
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date of publication",
    )
    tweet_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Tweet ID",
    )
    last_error = models.TextField(blank=True, default="", verbose_name="Last error")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tweet"
        verbose_name_plural = "Tweets"

    def __str__(self):
        return f"{self.content[:30]}... ({self.status})"


class TwitterCredentials(models.Model):
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="twitter_credentials",
        verbose_name=_("User"),
    )
    api_key = models.CharField(_("API Key"), max_length=255)
    api_secret_key = models.CharField(_("API Secret Key"), max_length=255)
    access_token = models.CharField(_("Access Token"), max_length=255)
    access_token_secret = models.CharField(_("Access Token Secret"), max_length=255)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Twitter Credentials")
        verbose_name_plural = _("Twitter Credentials")

    def __str__(self):
        return f"Twitter credentials for {self.user.username}"
