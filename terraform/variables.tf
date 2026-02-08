variable "project_name" {
  default = "event-driven-reporting-pipeline"
}

variable "event_source" {
  default = "application_A"
}

variable "daily_report_schedule_expression" {
  default = "cron(0 0 * * ? *)"
}
