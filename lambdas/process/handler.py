import json
import os
import logging
from datetime import datetime, timezone
from urllib.parse import unquote_plus

try:
    import boto3
except ImportError:  # Makes local import/testing possible even without AWS libs installed.
    boto3 = None

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _get_s3_client():
    if boto3 is None:
        raise RuntimeError("boto3 is required to run this Lambda handler")
    return boto3.client("s3")


def lambda_handler(event, context):
    """
    Processes raw data from S3 by adding metadata and storing in processed bucket.
    Triggered by S3 ObjectCreated events.
    
    Args:
        event: S3 event notification
        context: Lambda context object
    
    Returns:
        dict: Status and number of records processed
    """
    try:
        s3 = _get_s3_client()

        # Validate required environment variables
        processed_bucket = os.environ.get("PROCESSED_BUCKET")
        if not processed_bucket:
            logger.error("Missing required environment variable: PROCESSED_BUCKET")
            raise RuntimeError("PROCESSED_BUCKET environment variable not configured")

        # Validate event structure
        if not isinstance(event, dict):
            logger.error("Invalid event payload: expected dict")
            return {
                "statusCode": 400,
                "status": "error",
                "message": "Invalid event payload"
            }

        records = event.get("Records", [])
        if not records:
            logger.warning("No records found in event")
            return {
                "statusCode": 200,
                "status": "no_records",
                "records_processed": 0
            }
        
        processed_count = 0
        errors = []
        
        for idx, record in enumerate(records):
            try:
                # Validate record structure
                if "s3" not in record:
                    logger.warning(f"Record {idx} missing 's3' field, skipping")
                    errors.append(f"Record {idx}: Missing s3 field")
                    continue
                
                bucket = record["s3"]["bucket"]["name"]
                raw_key = record["s3"]["object"]["key"]
                key = unquote_plus(raw_key)

                logger.info(f"Processing object: s3://{bucket}/{key}")

                # Read raw data from S3
                obj = s3.get_object(Bucket=bucket, Key=key)
                data = json.loads(obj["Body"].read().decode("utf-8"))

                # Keep output JSON-object shaped even if source payload is not an object.
                if not isinstance(data, dict):
                    data = {"payload": data}

                # Add processing metadata
                data["processed"] = True
                data["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
                if context and getattr(context, "aws_request_id", None):
                    data["lambda_request_id"] = context.aws_request_id

                # Generate new key for processed data
                if key.startswith("raw/"):
                    new_key = f"processed/{key[len('raw/'):]}"
                else:
                    new_key = f"processed/{key.lstrip('/')}"

                # Store processed data
                s3.put_object(
                    Bucket=processed_bucket,
                    Key=new_key,
                    Body=json.dumps(data),
                    ContentType="application/json"
                )
                
                logger.info(f"Successfully processed: {new_key}")
                processed_count += 1
                
            except KeyError as e:
                error_msg = f"Record {idx}: Missing required field {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except json.JSONDecodeError as e:
                error_msg = f"Record {idx}: Invalid JSON in source object"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Record {idx}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        result = {
            "statusCode": 200 if not errors else 207,  # 207 = Multi-Status
            "status": "processed",
            "records_processed": processed_count,
            "total_records": len(records)
        }
        
        if errors:
            result["errors"] = errors
            logger.warning(f"Processing completed with {len(errors)} error(s)")
        else:
            logger.info(f"Successfully processed all {processed_count} record(s)")
        
        return result
    
    except Exception as e:
        logger.error(f"Fatal error in lambda_handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "status": "error",
            "message": str(e)
        }
