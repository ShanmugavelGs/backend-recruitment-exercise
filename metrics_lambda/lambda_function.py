import json
import os
from datetime import datetime
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda function to store agent metrics in DynamoDB.
    
    Expected event structure:
    {
        "run_id": "uuid-string",
        "agent_name": "rag-module",
        "tokens_consumed": 150,
        "tokens_generated": 50,
        "response_time_ms": 1200,
        "confidence_score": 0.85,
        "status": "success"
    }
    """
    try:
        # Initialize DynamoDB client
        region = os.getenv("AWS_REGION", "us-east-1")
        table_name = os.getenv("DYNAMODB_TABLE_METRICS", "AgentMetrics")
        
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=region
        )
        
        table = dynamodb.Table(table_name)
        
        # Parse the event
        if "body" in event:
            event = json.loads(event["body"])
        if isinstance(event, str):
            event = json.loads(event)
        
        # Validate required fields
        required_fields = [
            "run_id", "agent_name", "tokens_consumed", 
            "tokens_generated", "response_time_ms", "confidence_score", "status"
        ]
        
        for field in required_fields:
            if field not in event:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"Missing required field: {field}"
                    })
                }
        
        # Prepare item for DynamoDB
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        item = {
            "run_id": event["run_id"],
            "timestamp": timestamp,
            "agent_name": event["agent_name"],
            "tokens_consumed": int(event["tokens_consumed"]),
            "tokens_generated": int(event["tokens_generated"]),
            "response_time_ms": int(event["response_time_ms"]),
            "confidence_score": Decimal(str(event["confidence_score"])),
            "status": event["status"]
        }
        
        # Add any additional metadata
        for key, value in event.items():
            if key not in item and key not in required_fields:
                item[key] = value
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Metrics stored successfully",
                "run_id": event["run_id"],
                "timestamp": timestamp
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"DynamoDB error: {error_code} - {error_message}"
            })
        }
        
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Invalid input: {str(e)}"
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}"
            })
        }


