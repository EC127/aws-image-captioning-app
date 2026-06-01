"""
Caption-generation Lambda function for the AWS Image Captioning project.

This function is triggered by an Amazon EventBridge S3 ObjectCreated event.
It downloads the uploaded image from S3, sends the image to the Gemini API,
and stores the generated caption in Amazon RDS MySQL.

Sensitive deployment values must be provided through Lambda environment
variables. Do not hardcode API keys, database passwords, bucket names,
RDS endpoints, AWS account IDs, or other private configuration in this file.
"""

import base64
import json
import os

import boto3
import pymysql
import requests


s3 = boto3.client("s3")

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_API_URL = os.environ.get(
    "GEMINI_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
)

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")
SKIPPED_PREFIXES = ("thumbnails/", "captions/")


def lambda_handler(event, context):
    """Handle an EventBridge S3 event and generate a caption for the uploaded image."""
    print("Received event:", json.dumps(event))

    key = event.get("detail", {}).get("object", {}).get("key", "")
    bucket = event.get("detail", {}).get("bucket", {}).get("name", "")

    if (
        key.startswith(SKIPPED_PREFIXES)
        or not key.lower().endswith(ALLOWED_EXTENSIONS)
    ):
        print("Skipped key:", key)
        return {"statusCode": 200, "body": "Skipped file."}

    try:
        image_obj = s3.get_object(Bucket=bucket, Key=key)
        image_data = image_obj["Body"].read()
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Describe this image."},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_b64,
                            }
                        },
                    ]
                }
            ]
        }

        response = requests.post(
            url=f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=20,
        )
        response.raise_for_status()

        result = response.json()
        print("Gemini API response received.")

        caption = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "No caption")
        )
        print(f"Caption generated for {key}.")

        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=5,
        )

        try:
            with connection.cursor() as cursor:
                insert_sql = "INSERT INTO captions (image_key, caption) VALUES (%s, %s)"
                cursor.execute(insert_sql, (key, caption))
            connection.commit()
        finally:
            connection.close()

        return {
            "statusCode": 200,
            "body": json.dumps("Caption generated and saved to RDS."),
        }

    except Exception as exc:
        print("Error:", str(exc))
        return {"statusCode": 500, "body": str(exc)}
