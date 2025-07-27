import os
from datetime import datetime
from typing import Optional, Dict
import boto3
from botocore.exceptions import ClientError
from .models import DocumentMetadata


class DynamoDBService:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.table_name = os.getenv("DYNAMODB_TABLE_DOCUMENTS", "DocumentsMetadata")
        
        # Configure DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.region,
        )
        
        self.table = self.dynamodb.Table(self.table_name)
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        try:
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self._create_table()
            else:
                raise

    def _create_table(self):
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'doc_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'doc_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            self.table = table
        except Exception as e:
            print(f"Failed to create table: {str(e)}")
            raise

    async def create_document(self, doc_id: str, filename: str, 
                            tags: Optional[Dict[str, str]] = None,
                            s3_key: Optional[str] = None) -> DocumentMetadata:
        timestamp = datetime.utcnow()
        
        item = {
            'doc_id': doc_id,
            'filename': filename,
            'upload_timestamp': timestamp.isoformat(),
        }
        
        if tags:
            item['tags'] = tags
        if s3_key:
            item['s3_key'] = s3_key

        try:
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(doc_id)'
            )
            
            return DocumentMetadata(
                doc_id=doc_id,
                filename=filename,
                upload_timestamp=timestamp,
                tags=tags,
                s3_key=s3_key
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Document with ID {doc_id} already exists")
            raise

    async def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        try:
            response = self.table.get_item(Key={'doc_id': doc_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return DocumentMetadata(
                doc_id=item['doc_id'],
                filename=item['filename'],
                upload_timestamp=datetime.fromisoformat(item['upload_timestamp']),
                tags=item.get('tags'),
                s3_key=item.get('s3_key')
            )
        except Exception as e:
            print(f"Failed to get document {doc_id}: {str(e)}")
            return None

    async def update_document(self, doc_id: str, 
                            tags: Optional[Dict[str, str]] = None,
                            filename: Optional[str] = None) -> Optional[DocumentMetadata]:
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        if filename:
            update_expression_parts.append("#fn = :filename")
            expression_attribute_names["#fn"] = "filename"
            expression_attribute_values[":filename"] = filename

        if tags is not None:
            if tags:
                update_expression_parts.append("#tags = :tags")
                expression_attribute_names["#tags"] = "tags"
                expression_attribute_values[":tags"] = tags
            else:
                update_expression_parts.append("REMOVE #tags")
                expression_attribute_names["#tags"] = "tags"

        if not update_expression_parts:
            return await self.get_document(doc_id)

        update_expression = "SET " + ", ".join(update_expression_parts)

        try:
            response = self.table.update_item(
                Key={'doc_id': doc_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
                ExpressionAttributeValues=expression_attribute_values if expression_attribute_values else None,
                ConditionExpression='attribute_exists(doc_id)',
                ReturnValues='ALL_NEW'
            )
            
            item = response['Attributes']
            return DocumentMetadata(
                doc_id=item['doc_id'],
                filename=item['filename'],
                upload_timestamp=datetime.fromisoformat(item['upload_timestamp']),
                tags=item.get('tags'),
                s3_key=item.get('s3_key')
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return None
            raise

    async def delete_document(self, doc_id: str) -> bool:
        try:
            self.table.delete_item(
                Key={'doc_id': doc_id},
                ConditionExpression='attribute_exists(doc_id)'
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise

    async def document_exists(self, doc_id: str) -> bool:
        document = await self.get_document(doc_id)
        return document is not None