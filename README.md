# Event-Driven Reporting Pipeline

## Overview
The **Event-Driven Reporting Pipeline** is a fully serverless system built on AWS that automatically ingests incoming events, processes data, and generates daily summary reports without manual intervention.

The system follows **event-driven architecture principles**, ensuring scalability, low cost, and minimal operational overhead. All infrastructure is provisioned using **Terraform**, and deployments are controlled via **GitHub Actions**.

---

## Problem Statement
In many organizations:
- Data arrives continuously from applications or services
- Processing scripts are triggered manually
- Reports are generated inconsistently

This project solves these problems by creating a **fully automated pipeline** that reacts to events, processes data, and produces daily reports reliably.

---

## Type of Data Handled
The system processes **structured JSON events**, representing application or system activities.

### Example Event
```json
{
  "event_id": "12345",
  "source": "application_A",
  "timestamp": "2026-02-08T10:30:00Z",
  "event_type": "user_action",
  "details": {
    "action": "login",
    "status": "success"
  }
}
```

---

## How the System Works

1. **Event Ingestion**
   - External systems send JSON events to Amazon EventBridge.
   - EventBridge routes events based on predefined rules.

2. **Raw Data Storage**
   - An ingestion Lambda function stores incoming events in an S3 bucket as raw data.

3. **Data Processing**
   - A processing Lambda is triggered when new data is stored.
   - The data is transformed and saved in a processed data bucket.

4. **Daily Reporting**
   - A scheduled EventBridge rule triggers a reporting Lambda once per day.
   - The report summarizes system activity and processing status.

5. **Automation**
   - All steps run automatically without manual intervention.

---

## Architecture Components
- **Amazon EventBridge** – Event routing and scheduling
- **AWS Lambda** – Serverless compute for ingestion, processing, and reporting
- **Amazon S3** – Durable storage for raw data, processed data, and reports
- **IAM** – Secure access control
- **Terraform** – Infrastructure as Code
- **GitHub Actions** – CI/CD automation

---

## Infrastructure Automation
All infrastructure is provisioned using **Terraform**, enabling:
- Version-controlled infrastructure
- Repeatable deployments
- Easy teardown to avoid unnecessary cost

---

## CI/CD Pipeline
The GitHub Actions workflow provides:
- Manual **Terraform Apply** button
- Manual **Terraform Destroy** button
- Controlled infrastructure changes

This mirrors real-world DevOps deployment practices.

---

## Cost Estimation
The solution is designed to remain within the AWS Free Tier for low workloads.

Estimated monthly cost:
- AWS Lambda: Free tier
- Amazon EventBridge: Free tier
- Amazon S3: ₹2–₹5
- GitHub Actions: Free tier

---

## Fault Tolerance and Scalability
- Automatic retries using Lambda
- Event-driven design avoids single points of failure
- S3 ensures high durability
- Scales automatically with incoming event volume

---

## Deployment Steps
1. Clone the repository
2. Configure AWS credentials as GitHub Secrets
3. Open GitHub Actions
4. Run the workflow with:
   - `apply` to create infrastructure
   - `destroy` to clean up infrastructure

---

## Conclusion
The **Event-Driven Reporting Pipeline** demonstrates a clean, scalable, and cost-effective approach to building automated data processing systems using modern cloud-native services.
