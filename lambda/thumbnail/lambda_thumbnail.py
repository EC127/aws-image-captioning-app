"""
Thumbnail-generation Lambda function for the AWS Image Captioning project.

This function is triggered by an Amazon EventBridge S3 ObjectCreated event.
It downloads an uploaded image from S3, creates a 128x128 thumbnail, and
uploads the generated thumbnail to the thumbnails/ prefix in the same bucket.

Sensitive deployment values must not be hardcoded in this file.
"""

import io
import os

import boto3
from PIL import Image


s3 = boto3.client("s3")
THUMBNAIL_PREFIX = "thumbnails/"
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")


def lambda_handler(event, context):
    """Handle an EventBridge S3 event and generate a thumbnail for the uploaded image."""
    print("Received event:", event)

    try:
        bucket = event["detail"]["bucket"]["name"]
        key = event["detail"]["object"]["key"]

        if key.startswith(THUMBNAIL_PREFIX) or not key.lower().endswith(ALLOWED_EXTENSIONS):
            print("Skipped key:", key)
            return {"statusCode": 200, "body": "Skipped file."}

        image_obj = s3.get_object(Bucket=bucket, Key=key)
        image_data = image_obj["Body"].read()

        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((128, 128))

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        thumbnail_key = f"{THUMBNAIL_PREFIX}{os.path.basename(key)}"

        s3.upload_fileobj(
            buffer,
            bucket,
            thumbnail_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )

        print("Thumbnail created and uploaded:", thumbnail_key)
        return {"statusCode": 200, "body": "Thumbnail generated."}

    except Exception as exc:
        print("Error:", str(exc))
        return {"statusCode": 500, "body": str(exc)}
