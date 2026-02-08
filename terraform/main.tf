resource "random_id" "rand" {
  byte_length = 4
}

data "archive_file" "ingest_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/ingest/handler.py"
  output_path = "${path.module}/ingest.zip"
}

data "archive_file" "process_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/process/handler.py"
  output_path = "${path.module}/process.zip"
}

data "archive_file" "report_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/report/handler.py"
  output_path = "${path.module}/report.zip"
}

# S3 Buckets
resource "aws_s3_bucket" "raw" {
  bucket = "${var.project_name}-raw-${random_id.rand.hex}"
}

resource "aws_s3_bucket" "processed" {
  bucket = "${var.project_name}-processed-${random_id.rand.hex}"
}

resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-reports-${random_id.rand.hex}"
}

# Lambda Functions
resource "aws_lambda_function" "ingest" {
  function_name    = "${var.project_name}-ingest"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.ingest_zip.output_path
  source_code_hash = data.archive_file.ingest_zip.output_base64sha256

  depends_on = [
    aws_iam_role_policy_attachment.basic_logs,
    aws_iam_role_policy.lambda_s3_access
  ]

  environment {
    variables = {
      RAW_BUCKET = aws_s3_bucket.raw.bucket
    }
  }
}

resource "aws_lambda_function" "process" {
  function_name    = "${var.project_name}-process"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.process_zip.output_path
  source_code_hash = data.archive_file.process_zip.output_base64sha256

  depends_on = [
    aws_iam_role_policy_attachment.basic_logs,
    aws_iam_role_policy.lambda_s3_access
  ]

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed.bucket
    }
  }
}

resource "aws_lambda_function" "report" {
  function_name    = "${var.project_name}-report"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.report_zip.output_path
  source_code_hash = data.archive_file.report_zip.output_base64sha256

  depends_on = [
    aws_iam_role_policy_attachment.basic_logs,
    aws_iam_role_policy.lambda_s3_access
  ]

  environment {
    variables = {
      REPORT_BUCKET = aws_s3_bucket.reports.bucket
    }
  }
}

# EventBridge -> Ingest Lambda
resource "aws_cloudwatch_event_rule" "ingest_events" {
  name = "${var.project_name}-ingest-events"
  event_pattern = jsonencode({
    source = [var.event_source]
  })
}

resource "aws_cloudwatch_event_target" "ingest_target" {
  rule = aws_cloudwatch_event_rule.ingest_events.name
  arn  = aws_lambda_function.ingest.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke_ingest" {
  statement_id  = "AllowExecutionFromEventBridgeIngest"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingest_events.arn
}

# S3 Raw Bucket -> Process Lambda
resource "aws_lambda_permission" "allow_s3_invoke_process" {
  statement_id  = "AllowExecutionFromRawBucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw.arn
}

resource "aws_s3_bucket_notification" "raw_to_process" {
  bucket = aws_s3_bucket.raw.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke_process]
}

# Daily Schedule -> Report Lambda
resource "aws_cloudwatch_event_rule" "daily_report" {
  name                = "${var.project_name}-daily-report"
  schedule_expression = var.daily_report_schedule_expression
}

resource "aws_cloudwatch_event_target" "report_target" {
  rule = aws_cloudwatch_event_rule.daily_report.name
  arn  = aws_lambda_function.report.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke_report" {
  statement_id  = "AllowExecutionFromEventBridgeReport"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.report.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_report.arn
}
