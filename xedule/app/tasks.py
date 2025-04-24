import logging
import time

import tweepy
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Tweet

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


@shared_task
def publish_tweet():
    client = tweepy.Client(
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET_KEY,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    )

    pending_tweets = Tweet.objects.filter(
        status="pending",
        scheduled_time__lte=timezone.now(),
    )

    if not pending_tweets.exists():
        return "There are no tweets pending to be published."

    published_count = 0

    for tweet in pending_tweets:
        retries = 0
        success = False

        while retries < MAX_RETRIES and not success:
            try:
                response = client.create_tweet(text=tweet.content)

                tweet.status = "published"
                tweet.published_at = timezone.now()
                tweet.tweet_id = response.data["id"]
                tweet.last_error = ""
                tweet.save()

                published_count += 1
                success = True
                logger.error("Tweet %s successfully published.", tweet.id)
            except tweepy.errors.TweepyException as e:
                tweet.last_error = str(e)
                tweet.save()
                retries += 1
                wait_time = BACKOFF_BASE**retries
                logger.exception(
                    "Error when posting tweet %(tweet_id)s: %(error)s - Retrying in %(wait_time)s seconds...",
                    extra={
                        "tweet_id": tweet.id,
                        "error": str(e),
                        "wait_time": wait_time,
                    },
                )
                time.sleep(wait_time)
            except Exception as e:
                tweet.last_error = str(e)
                tweet.save()
                logger.exception(
                    "Error inesperado al publicar tweet %(tweet_id)s",
                    extra={"tweet_id": tweet.id},
                )
                break  # Do not continue if it is an unexpected error

        if not success:
            logger.error(
                "Could not post the tweet %(tweet_id)s after %(max_retries)s attempts.",
                extra={"tweet_id": tweet.id, "max_retries": MAX_RETRIES},
            )

    return f"Se publicaron {published_count} tweets"


@shared_task
def schedule_pending_tweets():
    """
    Tarea periódica para revisar y publicar tweets programados
    """
    return publish_tweet.delay()
