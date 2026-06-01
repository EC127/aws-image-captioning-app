#!/bin/bash

dnf update -y
dnf install -y python3 python3-pip unzip

mkdir -p /opt/image-captioning-app
cd /opt/image-captioning-app

aws s3 cp s3://example-deployment-bucket/deployment/app.zip ./app.zip
unzip app.zip

python3 -m pip install -r requirements.txt

export DB_HOST="example-rds-endpoint"
export DB_USER="example-user"
export DB_PASSWORD="example-password"
export DB_NAME="image_caption_db"
export S3_BUCKET="example-bucket"

python3 app.py
