variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

variable "location" {
  description = "The Azure region."
  type        = string
}

variable "name" {
  description = "The name of the Automation Account."
  type        = string
}

variable "sku_name" {
  description = "The SKU of the Automation Account. Defaults to Basic."
  type        = string
  default     = "Basic"
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}

variable "subnet_id" {
  description = "The ID of the Subnet for the Private Endpoint."
  type        = string
}

variable "private_dns_zone_ids" {
  description = "A map or list of Private DNS Zone IDs for the Private Endpoint integration."
  type        = list(string)
  default     = []
}

variable "runbooks" {
  description = "A map of runbooks to create. Key is runbook name, value is configuration."
  type = map(object({
    runbook_type = string
    description  = optional(string)
  }))
  default = {}
}

variable "devops_pat" {
  description = "The Personal Access Token for Azure DevOps integration."
  type        = string
  sensitive   = true
}

variable "repository_url" {
  description = "The URL of the Azure DevOps repository."
  type        = string
}

variable "branch" {
  description = "The branch to sync from the source control."
  type        = string
  default     = "main"
}

variable "folder_path" {
  description = "The folder path in the repository that contains the runbooks."
  type        = string
}

variable "enable_public_network_access" {
  description = "Whether public network access is allowed for the automation account."
  type        = bool
  default     = false
}

variable "report_storage_account_id" {
  description = "The ID of the Storage Account for reports."
  type        = string
}

variable "report_storage_account_name" {
  description = "The Name of the Storage Account for reports."
  type        = string
}
