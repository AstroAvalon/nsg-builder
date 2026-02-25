variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

variable "location" {
  description = "The Azure region for the Private Endpoint (must match VNet region)."
  type        = string
}

variable "data_location" {
  description = "The location where the data is stored (e.g. United States)."
  type        = string
  default     = "United States"
}

variable "name" {
  description = "The name of the Communication Service."
  type        = string
}

variable "email_service_name" {
  description = "The name of the Email Communication Service."
  type        = string
}

variable "domain_name" {
  description = "The domain name (e.g. AzureManagedDomain)."
  type        = string
  default     = "AzureManagedDomain"
}

variable "subnet_id" {
  description = "The ID of the Subnet for the Private Endpoint."
  type        = string
}

variable "private_dns_zone_ids" {
  description = "A list of Private DNS Zone IDs for the Private Endpoint integration."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}
