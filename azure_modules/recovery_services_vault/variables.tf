variable "vault_name" {
  description = "The name of the Recovery Services Vault."
  type        = string
}

variable "location" {
  description = "The Azure region where the Recovery Services Vault should be created."
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group in which to create the Recovery Services Vault."
  type        = string
}

variable "resource_group_name_pep" {
  description = "The name of the resource group in which to create the Private Endpoint."
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnet where the Private Endpoint should be created."
  type        = string
}

variable "rv_zone_id" {
  description = "The ID of the primary Private DNS Zone for the Recovery Services Vault (e.g., privatelink.backup.windowsazure.com)."
  type        = string
}

variable "rv_zone_id_secondary" {
  description = "The ID of the secondary Private DNS Zone for the Recovery Services Vault (e.g., privatelink.backup.windowsazure.com)."
  type        = string
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
}

variable "backup_time" {
  description = "The time of day for the backup policy to run (e.g., 08:00). Defaults to 08:00."
  type        = string
  default     = "08:00"
}
