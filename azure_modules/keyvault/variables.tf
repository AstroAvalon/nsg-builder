variable "project" {
  description = "Project configuration details."
  type = object({
    customer_subscription_id = string
    location                 = string
    environment_level        = string
    customer                 = string
    client_code              = string
    availability_zone        = string
    address_space            = list(string)
  })
}

variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

variable "location" {
  description = "The location for the Key Vault."
  type        = string
}

variable "base_resource_name" {
  description = "The base name for resources (e.g., customer-client-loc-env)."
  type        = string
}

variable "subnet_id" {
  description = "The Subnet ID where the Private Endpoint will be created."
  type        = string
}

variable "private_dns_zone_ids" {
  description = "Map containing 'primary' and 'secondary' Private DNS Zone IDs for Key Vault."
  type        = map(string)
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}
