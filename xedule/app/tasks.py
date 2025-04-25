import logging
import time

import tweepy
from celery import shared_task
from django.utils import timezone

from xedule.users.models import User

from .models import Tweet
from .models import TwitterCredentials

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


@shared_task
def publish_tweet():
    """Process pending tweets and publish them to Twitter."""
    pending_tweets = Tweet.objects.filter(
        status="pending",
        scheduled_time__lte=timezone.now(),
    )

    if not pending_tweets.exists():
        return "There are no tweets pending to be published."

    # Group tweets by user
    grouped_tweets = _group_tweets_by_user(pending_tweets)

    # Process tweets by user
    published_count = _process_grouped_tweets(grouped_tweets)

    return f"Se publicaron {published_count} tweets"


def _group_tweets_by_user(tweets):
    """Group tweets by user_id."""
    grouped_tweets = {}
    for tweet in tweets:
        if tweet.user_id not in grouped_tweets:
            grouped_tweets[tweet.user_id] = []
        grouped_tweets[tweet.user_id].append(tweet)
    return grouped_tweets


def _process_grouped_tweets(grouped_tweets):
    """Process tweets grouped by user."""
    published_count = 0

    for user_id, user_tweets in grouped_tweets.items():
        try:
            user_published = _process_user_tweets(user_id, user_tweets)
            published_count += user_published
        except Exception:
            logger.exception("Error processing tweets for user %s", user_id)

    return published_count


def _process_user_tweets(user_id, user_tweets):
    """Process tweets for a specific user."""
    try:
        user = User.objects.get(id=user_id)
        credentials = TwitterCredentials.objects.get(user=user)
        client = _create_twitter_client(credentials)

        return _publish_user_tweets(user_tweets, client)

    except TwitterCredentials.DoesNotExist:
        _mark_tweets_with_error(
            user_tweets, "User does not have Twitter API credentials configured"
        )
        for tweet in user_tweets:
            logger.exception(
                "User %s does not have Twitter credentials configured. Tweet %s not published.",
                user_id,
                tweet.id,
            )
        return 0

    except User.DoesNotExist:
        _mark_tweets_with_error(user_tweets, "User does not exist")
        for tweet in user_tweets:
            logger.exception(
                "User %s does not exist. Tweet %s not published.",
                user_id,
                tweet.id,
            )
        return 0


def _create_twitter_client(credentials):
    """Create a Twitter API client using user credentials."""
    return tweepy.Client(
        consumer_key=credentials.api_key,
        consumer_secret=credentials.api_secret_key,
        access_token=credentials.access_token,
        access_token_secret=credentials.access_token_secret,
    )


def _publish_user_tweets(tweets, client):
    """Publish tweets for a user with the given client."""
    published_count = 0

    for tweet in tweets:
        if _publish_tweet_with_retry(tweet, client):
            published_count += 1

    return published_count


def _publish_tweet_with_retry(tweet, client):
    """Attempt to publish a tweet with retries."""
    retries = 0
    success = False

    while retries < MAX_RETRIES and not success:
        try:
            response = client.create_tweet(text=tweet.content)
            _update_published_tweet(tweet, response.data["id"])
            success = True
            logger.info("Tweet %s successfully published.", tweet.id)

        except tweepy.errors.TweepyException as e:
            _handle_tweepy_error(tweet, e, retries)
            retries += 1

        except Exception as e:
            _update_tweet_error(tweet, str(e))
            logger.exception(
                "Error inesperado al publicar tweet %(tweet_id)s",
                extra={"tweet_id": tweet.id},
            )
            break

    if not success:
        logger.error(
            "Could not post the tweet %(tweet_id)s after %(max_retries)s attempts.",
            extra={"tweet_id": tweet.id, "max_retries": MAX_RETRIES},
        )

    return success


def _update_published_tweet(tweet, tweet_id):
    """Update tweet status to published."""
    tweet.status = "published"
    tweet.published_at = timezone.now()
    tweet.tweet_id = tweet_id
    tweet.last_error = ""
    tweet.save()


def _handle_tweepy_error(tweet, error, retries):
    """Handle Tweepy API errors with exponential backoff."""
    _update_tweet_error(tweet, str(error))
    wait_time = BACKOFF_BASE**retries
    logger.exception(
        "Error when posting tweet %(tweet_id)s: %(error)s - Retrying in %(wait_time)s seconds...",
        extra={
            "tweet_id": tweet.id,
            "error": str(error),
            "wait_time": wait_time,
        },
    )
    time.sleep(wait_time)


def _update_tweet_error(tweet, error_message):
    """Update tweet with error message."""
    tweet.last_error = error_message
    tweet.save()


def _mark_tweets_with_error(tweets, error_message):
    """Mark multiple tweets with an error message."""
    for tweet in tweets:
        _update_tweet_error(tweet, error_message)


@shared_task
def schedule_pending_tweets():
    """
    Periodic task to check and publish scheduled tweets
    """
    return publish_tweet.delay()
