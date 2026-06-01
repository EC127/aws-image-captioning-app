# AWS Image Captioning Web Application

A cloud-based image annotation application deployed in an AWS Academy sandbox environment. The system allowed users to upload images through a Flask web application, store original images in Amazon S3, generate thumbnails asynchronously using AWS Lambda, generate image captions through the Gemini API, and store caption metadata in Amazon RDS MySQL.

> Deployment status: The original AWS Academy sandbox environment has expired. This repository provides a sanitised portfolio case study, architecture diagrams, implementation notes, and representative code snippets reconstructed from the completed project report.

## Tech Stack

- Backend: Python, Flask
- Cloud: AWS EC2, S3, RDS MySQL, Lambda, EventBridge, ALB, Auto Scaling Group, IAM, VPC, NAT Gateway, Security Groups
- AI API: Google Gemini REST API
- Database: MySQL
- Deployment environment: AWS Academy sandbox

## Architecture Overview

The application used two connected architectures:

1. Web application architecture:
   - Users accessed the Flask application through an Application Load Balancer.
   - EC2 instances were managed by an Auto Scaling Group.
   - Uploaded images were stored in the `uploads/` prefix of an S3 bucket.
   - Captions and image metadata were retrieved from RDS MySQL.

2. Serverless architecture:
   - S3 events were sent to Amazon EventBridge.
   - EventBridge triggered two Lambda functions when a new object was created under `uploads/`.
   - One Lambda function generated image thumbnails.
   - One Lambda function called the Gemini API and inserted captions into RDS.

## Key Features

- Image upload through Flask web interface
- S3-based storage for original images and thumbnails
- EventBridge-based event routing
- Separate Lambda functions for caption generation and thumbnail generation
- RDS MySQL metadata storage
- ALB and Auto Scaling Group for scalable web serving
- Bastion host and security group design for restricted database access

## Security Design

- RDS was placed in private subnets.
- RDS accepted MySQL traffic only from the application EC2 security group and bastion host security group.
- Administrative SSH access used a bastion host instead of exposing private instances directly.
- Lambda environment variables were used for external API and database configuration.
- S3 prefixes were separated into `uploads/` and `thumbnails/` to avoid recursive Lambda triggering.

## Limitations

- The live AWS environment is no longer available because the AWS Academy sandbox expired.
- API keys, credentials, resource identifiers, and account-specific configuration are excluded.
- Representative code snippets are provided for portfolio demonstration rather than direct redeployment.
- Infrastructure was configured manually through AWS Console and documented in the report; future improvement would be to automate it with Terraform or CloudFormation.

## Future Improvements

- Rebuild infrastructure using Terraform or CloudFormation
- Add CI/CD deployment pipeline
- Add authentication and user account support
- Add CloudWatch monitoring dashboards
- Improve error handling and retry logic for Lambda functions
- Add automated tests for Flask routes and Lambda handlers
