# Generated by Django 4.2.20 on 2025-05-01 20:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0003_tweet_nostr_id_tweet_publish_to_nostr_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=280, verbose_name='Contenido')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('published_x', 'Published in X'), ('published_n', 'Published in Nostr')], default='pending', max_length=12, verbose_name='State')),
                ('scheduled_time', models.DateTimeField(blank=True, null=True, verbose_name='Scheduled date and time')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date of creation')),
                ('published_at', models.DateTimeField(blank=True, null=True, verbose_name='Date of publication')),
                ('tweet_id', models.CharField(blank=True, default='', max_length=50, verbose_name='Note ID')),
                ('publish_to_nostr', models.BooleanField(default=False, verbose_name='Publish to Nostr')),
                ('publish_to_x', models.BooleanField(default=False, verbose_name='Publish to X')),
                ('nostr_id', models.CharField(blank=True, default='', max_length=64, verbose_name='Nostr ID')),
                ('last_error', models.TextField(blank=True, default='', verbose_name='Last error')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tweets', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Note',
                'verbose_name_plural': 'Tweets',
                'ordering': ['-created_at'],
            },
        ),
        migrations.DeleteModel(
            name='Tweet',
        ),
    ]
