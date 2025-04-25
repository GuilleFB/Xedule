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


def get_twitter_client():
    """Create and return a Twitter API client."""
    return tweepy.Client(
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET_KEY,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    )


def get_pending_tweets():
    """Retrieve tweets that are ready to be published."""
    return Tweet.objects.filter(
        status="pending",
        scheduled_time__lte=timezone.now(),
    )


def post_single_tweet(client, tweet):
    """
    Attempt to post a single tweet with retry logic.
    Returns a tuple of (success_status, error_message)
    """
    for retry in range(MAX_RETRIES):
        try:
            response = client.create_tweet(text=tweet.content)

            # Update tweet record on success
            tweet.status = "published"
            tweet.published_at = timezone.now()
            tweet.tweet_id = response.data["id"]
            tweet.last_error = ""
            tweet.save()
        except tweepy.errors.TweepyException as e:
            error_message = str(e)
            tweet.last_error = error_message
            tweet.save()

            wait_time = BACKOFF_BASE ** (retry + 1)
            logger.exception(
                "Error when posting tweet %(tweet_id)s: %(error)s - Retrying in %(wait_time)s seconds...",
                extra={
                    "tweet_id": tweet.id,
                    "error": error_message,
                    "wait_time": wait_time,
                },
            )
            time.sleep(wait_time)
            continue
        except Exception as e:
            error_message = str(e)
            tweet.last_error = error_message
            tweet.save()

            logger.exception(
                "Error inesperado al publicar tweet %(tweet_id)s",
                extra={"tweet_id": tweet.id},
            )
            return False, error_message
        else:
            # This block executes if no exception occurs in the try block
            logger.info("Tweet %s successfully published.", tweet.id)
            return True, None

    # If we've exhausted all retries
    logger.error(
        "Could not post the tweet %(tweet_id)s after %(max_retries)s attempts.",
        extra={"tweet_id": tweet.id, "max_retries": MAX_RETRIES},
    )
    return False, tweet.last_error


@shared_task
def publish_tweet():
    """
    Task to publish pending tweets.
    Returns a status message about how many tweets were published.
    """
    client = get_twitter_client()
    pending_tweets = get_pending_tweets()

    if not pending_tweets.exists():
        return "There are no tweets pending to be published."

    published_count = 0

    for tweet in pending_tweets:
        success, _ = post_single_tweet(client, tweet)
        if success:
            published_count += 1

    return f"Se publicaron {published_count} tweets"


@shared_task
def schedule_pending_tweets():
    """
    Periodic task to check and publish scheduled tweets
    """
    return publish_tweet.delay()
