variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

variable "location" {
  description = "The Azure region."
  type        = string
}

variable "name" {
  description = "The name of the Logic App."
  type        = string
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}

variable "storage_account_name" {
  description = "The name of the Storage Account for the API Connection."
  type        = string
}

variable "storage_account_id" {
  description = "The ID of the Storage Account for the Event Grid Topic."
  type        = string
}

variable "storage_account_access_key" {
  description = "The primary access key of the Storage Account for the API Connection."
  type        = string
  sensitive   = true
}
