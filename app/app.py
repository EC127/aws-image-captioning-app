"""
Sanitised Flask application for the AWS Image Captioning Web Application.

This version is prepared for portfolio/GitHub use. Credentials, account-specific
resource identifiers, and deployment-specific values have been replaced with
environment variables or placeholders.
"""

import os
from pathlib import Path

import boto3
import mysql.connector
from flask import Flask, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename


app = Flask(__name__)

# AWS and application configuration.
# Set these values in the deployment environment instead of hardcoding them.
S3_BUCKET = os.environ.get("S3_BUCKET", "your-s3-bucket-name")
UPLOAD_PREFIX = os.environ.get("UPLOAD_PREFIX", "uploads/")
THUMBNAIL_PREFIX = os.environ.get("THUMBNAIL_PREFIX", "thumbnails/")

# RDS MySQL configuration.
DB_HOST = os.environ.get("DB_HOST", "your-rds-endpoint")
DB_NAME = os.environ.get("DB_NAME", "image_caption_db")
DB_USER = os.environ.get("DB_USER", "your-db-user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "your-db-password")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

s3_client = boto3.client("s3")


def get_db_connection():
    """
    Establish a connection to the MySQL RDS database.

    Returns:
        mysql.connector.connection.MySQLConnection | None:
        Database connection object, or None if connection fails.
    """
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        return None


def allowed_file(filename):
    """
    Check whether an uploaded file has an allowed image extension.

    Args:
        filename: Uploaded filename.

    Returns:
        bool: True if the extension is allowed, otherwise False.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_s3_public_url(prefix, filename):
    """
    Build a public S3 object URL for portfolio/demo display.

    This assumes the relevant S3 objects are publicly readable or served through
    another public access mechanism.
    """
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{prefix}{filename}"


def filename_to_image_key(filename):
    """Convert a display filename into the S3 object key stored in RDS."""
    return f"{UPLOAD_PREFIX}{filename}"


@app.route("/")
def upload_form():
    """Render the homepage with the file upload form."""
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload_image():
    """
    Handle image upload.

    The uploaded image is validated, stored under the S3 uploads/ prefix,
    and then displayed on the upload result page.
    """
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part in the request", 400

        file = request.files["file"]

        if file.filename == "":
            return "No selected file", 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            object_key = filename_to_image_key(filename)

            s3_client.upload_fileobj(
                file,
                S3_BUCKET,
                object_key,
                ExtraArgs={"ACL": "public-read"},
            )

            return redirect(url_for("view_image", filename=filename))

        return "Unsupported file type", 400

    return redirect(url_for("upload_form"))


@app.route("/upload/<filename>")
def view_image(filename):
    """
    Display the uploaded original image, generated thumbnail, and caption.

    Args:
        filename: Name of the uploaded image.
    """
    original_url = build_s3_public_url(UPLOAD_PREFIX, filename)
    thumbnail_url = build_s3_public_url(THUMBNAIL_PREFIX, filename)
    image_key = filename_to_image_key(filename)
    caption = "Caption not yet available"

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT caption FROM captions WHERE image_key = %s",
                    (image_key,),
                )
                result = cursor.fetchone()
                if result:
                    caption = result[0]
        except mysql.connector.Error as err:
            print("Error fetching caption from database:", err)
        finally:
            conn.close()

    return render_template(
        "upload.html",
        filename=filename,
        original_url=original_url,
        thumbnail_url=thumbnail_url,
        caption=caption,
    )


@app.route("/gallery")
def gallery():
    """
    Display uploaded images with thumbnails and captions.

    Gallery entries are loaded from the captions table. The table stores the
    uploaded image object key, for example uploads/example.jpg.
    """
    images = []

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT image_key, caption FROM captions")
                for image_key, caption in cursor.fetchall():
                    filename = Path(image_key).name
                    images.append(
                        {
                            "filename": filename,
                            "original_url": build_s3_public_url(UPLOAD_PREFIX, filename),
                            "thumbnail_url": build_s3_public_url(
                                THUMBNAIL_PREFIX,
                                filename,
                            ),
                            "caption": caption,
                        }
                    )
        except mysql.connector.Error as err:
            print("Error retrieving gallery data:", err)
        finally:
            conn.close()

    return render_template("gallery.html", images=images)


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
