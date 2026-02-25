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

variable "app_service_plan_name" {
  description = "The name of the App Service Plan."
  type        = string
}

variable "storage_account_name" {
  description = "The name of the Storage Account for Logic App state."
  type        = string
}

variable "sku_tier" {
  description = "The SKU Tier for the App Service Plan (Workflow Standard)."
  type        = string
  default     = "WorkflowStandard"
}

variable "sku_size" {
  description = "The SKU Size for the App Service Plan (WS1)."
  type        = string
  default     = "WS1"
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}

variable "subnet_id_integration" {
  description = "The ID of the Subnet for VNet Integration (must be delegated to Microsoft.Web/serverFarms)."
  type        = string
}

variable "subnet_id_pe" {
  description = "The ID of the Subnet for the Private Endpoint."
  type        = string
}

variable "private_dns_zone_ids" {
  description = "A list of Private DNS Zone IDs for the Logic App Private Endpoint."
  type        = list(string)
  default     = []
}

variable "app_settings" {
  description = "A map of additional App Settings."
  type        = map(string)
  default     = {}
}
