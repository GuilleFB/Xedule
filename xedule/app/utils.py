# app/utils.py
from datetime import datetime

import pandas as pd
from django.utils import timezone

from .models import Tweet

TWEET_LENGTH = 280


def process_excel_file(excel_file, user):
    """
    Process the uploaded Excel file and create Tweet objects

    Expected columns:
    - content: The tweet text (required)
    - scheduled_time: When to publish the tweet (optional, format: YYYY-MM-DD HH:MM:SS)
    """
    # Load the Excel file
    tweets_data = load_excel_file(excel_file)
    if not tweets_data.get("success"):
        return tweets_data

    # Check required columns
    if "content" not in tweets_data["data"].columns:
        return {
            "success": False,
            "message": "The Excel file must have a 'content' column",
        }

    # Process rows
    return process_tweets_data(tweets_data["data"], user)


def load_excel_file(excel_file):
    try:
        tweets_data = pd.read_excel(excel_file)
    except (FileNotFoundError, ValueError, pd.errors.ExcelFileError) as e:
        return {"success": False, "message": f"Error reading Excel file: {e!s}"}
    else:
        return {"success": True, "data": tweets_data}


def process_tweets_data(tweets_data, user):
    tweets_created = 0
    tweets_failed = 0
    error_messages = []

    for index, row in tweets_data.iterrows():
        result = process_single_row(index, row, tweets_data, user)
        if result["success"]:
            tweets_created += 1
        else:
            tweets_failed += 1
            error_messages.append(result["message"])

    return {
        "success": True,
        "tweets_created": tweets_created,
        "tweets_failed": tweets_failed,
        "error_messages": error_messages,
    }


def process_single_row(index, row, tweets_data, user):
    if pd.isna(row.get("content", "")):
        return {"success": False, "message": f"Row {index + 2}: Empty content"}

    content = str(row["content"]).strip()
    if len(content) > TWEET_LENGTH:
        return {
            "success": False,
            "message": f"Row {index + 2}: Content exceeds 280 characters",
        }

    scheduled_time = handle_scheduled_time(index, row, tweets_data)
    if scheduled_time.get("error"):
        return {"success": False, "message": scheduled_time["error"]}

    try:
        Tweet.objects.create(
            user=user,
            content=content,
            scheduled_time=scheduled_time.get("time"),
            status="pending",
        )
    except (ValueError, TypeError, pd.errors.PandasError) as e:
        return {"success": False, "message": f"Row {index + 2}: {e!s}"}
    else:
        return {"success": True}


def handle_scheduled_time(index, row, tweets_data):
    if "scheduled_time" not in tweets_data.columns or pd.isna(row["scheduled_time"]):
        return {"time": None}

    try:
        if isinstance(row["scheduled_time"], datetime):
            scheduled_time = row["scheduled_time"]
        else:
            scheduled_time = pd.to_datetime(row["scheduled_time"])

        if scheduled_time.tzinfo is None:
            scheduled_time = timezone.make_aware(scheduled_time)
    except (ValueError, TypeError) as e:
        return {"error": f"Row {index + 2}: Invalid date format - {e!s}"}
    else:
        return {"time": scheduled_time}
