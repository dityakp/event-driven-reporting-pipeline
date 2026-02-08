import json
import boto3
import os
import uuid
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
RAW_BUCKET = os.environ.get("RAW_BUCKET")


def lambda_handler(event, context):
    """
    Ingests incoming events from EventBridge and stores them in S3 raw bucket.
    
    Args:
        event: EventBridge event data
        context: Lambda context object
    
    Returns:
        dict: Status and S3 key of stored object
    """
    try:
        # Validate required environment variables
        if not RAW_BUCKET:
            logger.error("Missing required environment variable: RAW_BUCKET")
            raise RuntimeError("RAW_BUCKET environment variable not configured")
        
        # Validate event data
        if not event:
            logger.warning("Received empty event")
            return {
                "statusCode": 400,
                "status": "error",
                "message": "Empty event received"
            }
        
        # Generate unique key for this event
        key = f"raw/{uuid.uuid4()}.json"
        
        logger.info(f"Ingesting event to S3: {key}")
        
        # Store event in S3
        s3.put_object(
            Bucket=RAW_BUCKET,
            Key=key,
            Body=json.dumps(event),
            ContentType="application/json"
        )
        
        logger.info(f"Successfully ingested event to {key}")
        
        return {
            "statusCode": 200,
            "status": "ingested",
            "s3_key": key
        }
    
    except Exception as e:
        logger.error(f"Error ingesting event: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "status": "error",
            "message": str(e)
        }
