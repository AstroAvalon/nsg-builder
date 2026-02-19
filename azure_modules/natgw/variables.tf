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
  description = "The Azure region where resources will be created."
  type        = string
}

variable "base_resource_name" {
  description = "The base name for resources."
  type        = string
}

variable "subnet_ids" {
  description = "A map of subnet IDs to associate with the NAT Gateway."
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}
