variable "resource_group_name" {
  description = "The name of the resource group for primary DNS zones."
  type        = string
}

variable "vnet_id" {
  description = "The ID of the Virtual Network to link the primary DNS zones to."
  type        = string
}

variable "secondary_location" {
  description = "The secondary location for the secondary DNS zones."
  type        = string
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}

variable "secondary_resource_group_name" {
  description = "The name of the resource group for secondary DNS zones. If not provided, it defaults to '<primary-rg-name>-secondary-dns'."
  type        = string
  default     = null
}
