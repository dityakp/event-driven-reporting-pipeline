resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_s3_access" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.raw.arn,
      aws_s3_bucket.processed.arn,
      aws_s3_bucket.reports.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.raw.arn}/*",
      "${aws_s3_bucket.processed.arn}/*",
      "${aws_s3_bucket.reports.arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_s3_access" {
  name   = "${var.project_name}-lambda-s3-access"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_s3_access.json
}
