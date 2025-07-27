#!/usr/bin/env python3
"""
Deployment script for the Agent-Metrics Lambda function.
This script creates the Lambda function and necessary IAM resources.
"""

import os
import json
import boto3
from botocore.exceptions import ClientError


def create_lambda_execution_role(iam_client, role_name: str) -> str:
    """Create IAM role for Lambda execution."""
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for Agent-Metrics Lambda function"
        )
        role_arn = response['Role']['Arn']
        print(f"Created IAM role: {role_arn}")
        
        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        # Create and attach DynamoDB policy
        dynamodb_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:CreateTable",
                        "dynamodb:DescribeTable"
                    ],
                    "Resource": "arn:aws:dynamodb:*:*:table/AgentMetrics"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="DynamoDBAccess",
            PolicyDocument=json.dumps(dynamodb_policy)
        )
        
        return role_arn
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            response = iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            raise


def create_lambda_function(lambda_client, function_name: str, role_arn: str, zip_path: str):
    """Create or update the Lambda function."""
    
    with open(zip_path, 'rb') as zip_file:
        zip_content = zip_file.read()
    
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Store agent metrics in DynamoDB',
            Timeout=30,
            MemorySize=128,
            Environment={
                'Variables': {
                    'DYNAMODB_TABLE_METRICS': 'AgentMetrics',
                    'CREATE_TABLE_IF_NOT_EXISTS': 'true'
                }
            }
        )
        print(f"Created Lambda function: {response['FunctionArn']}")
        return response['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            # Function exists, update it
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            print(f"Updated Lambda function: {response['FunctionArn']}")
            return response['FunctionArn']
        else:
            raise


def main():
    """Deploy the Lambda function."""
    
    # Configuration
    function_name = "store-agent-metrics"
    role_name = "AgentMetricsLambdaRole"
    zip_path = "function.zip"
    region = os.getenv("AWS_REGION", "us-east-1")
    
    # Check if deployment package exists
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found. Run build.sh first.")
        return 1
    
    try:
        # Initialize AWS clients
        iam_client = boto3.client('iam', region_name=region)
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Create IAM role
        print("Creating IAM role...")
        role_arn = create_lambda_execution_role(iam_client, role_name)
        
        # Wait a bit for role to propagate
        import time
        time.sleep(10)
        
        # Create Lambda function
        print("Creating Lambda function...")
        function_arn = create_lambda_function(lambda_client, function_name, role_arn, zip_path)
        
        # Create function URL (for HTTP access)
        try:
            url_response = lambda_client.create_function_url_config(
                FunctionName=function_name,
                AuthType='NONE',
                Cors={
                    'AllowCredentials': False,
                    'AllowHeaders': ['*'],
                    'AllowMethods': ['POST'],
                    'AllowOrigins': ['*'],
                    'ExposeHeaders': ['*'],
                    'MaxAge': 86400
                }
            )
            print(f"Function URL: {url_response['FunctionUrl']}")
            print(f"Set METRICS_LAMBDA_URL={url_response['FunctionUrl']} in your RAG module environment")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                url_response = lambda_client.get_function_url_config(FunctionName=function_name)
                print(f"Function URL (existing): {url_response['FunctionUrl']}")
            else:
                print(f"Warning: Could not create function URL: {e}")
        
        print("Deployment completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())