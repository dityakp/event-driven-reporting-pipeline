import os
import json
import datetime
import logging
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
REPORT_BUCKET = os.environ.get("REPORT_BUCKET")


def lambda_handler(event, context):
    """
    Generates daily summary report and stores it in S3 reports bucket.
    Triggered by EventBridge scheduled rule.
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context object
    
    Returns:
        dict: Status of report generation
    """
    try:
        # Validate required environment variables
        if not REPORT_BUCKET:
            logger.error("Missing required environment variable: REPORT_BUCKET")
            raise RuntimeError("REPORT_BUCKET environment variable not configured")
        
        # Generate report data
        report_date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        
        report = {
            "date": report_date,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "message": "Daily processing completed successfully",
            "lambda_request_id": context.aws_request_id,
            "function_version": context.function_version
        }
        
        report_key = f"reports/report-{report_date}.json"
        
        logger.info(f"Generating daily report for {report_date}")
        
        # Store report in S3
        s3.put_object(
            Bucket=REPORT_BUCKET,
            Key=report_key,
            Body=json.dumps(report, indent=2),
            ContentType="application/json"
        )
        
        logger.info(f"Successfully created report: {report_key}")
        
        return {
            "statusCode": 200,
            "status": "report_created",
            "report_date": report_date,
            "s3_key": report_key
        }
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "status": "error",
            "message": str(e)
        }
