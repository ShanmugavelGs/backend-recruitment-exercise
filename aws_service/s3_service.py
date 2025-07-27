import os
from typing import Optional
import boto3
from botocore.exceptions import ClientError


class S3Service:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1") 
        self.bucket_name = os.getenv("S3_BUCKET", "documents-rag-bucket")
        
        # Configure S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self._create_bucket()
            else:
                print(f"Error checking bucket: {str(e)}")
                raise

    def _create_bucket(self):
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
        except Exception as e:
            print(f"Failed to create bucket: {str(e)}")
            raise

    async def upload_file(self, doc_id: str, content: bytes, filename: str) -> str:
        s3_key = f"documents/{doc_id}/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType='application/pdf',
                Metadata={
                    'original_filename': filename,
                    'doc_id': doc_id
                }
            )
            return s3_key
        except Exception as e:
            raise ValueError(f"Failed to upload file to S3: {str(e)}")

    async def download_file(self, s3_key: str) -> Optional[bytes]:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    async def delete_file(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except Exception as e:
            print(f"Failed to delete file from S3: {str(e)}")
            return False

    async def file_exists(self, s3_key: str) -> bool:
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Failed to generate presigned URL: {str(e)}")
            return None