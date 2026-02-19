variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
}

variable "location" {
  description = "The Azure region where resources will be created."
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnet to attach the VM to."
  type        = string
}

variable "vm_name" {
  description = "The name of the Virtual Machine (max 15 chars for Windows compatibility)."
  type        = string
  validation {
    condition     = length(var.vm_name) <= 15
    error_message = "VM name must be 15 characters or less."
  }
}

variable "os_flavor" {
  description = "The OS flavor: 'rhel', 'win22', 'sql', 'win16'."
  type        = string
  validation {
    condition     = contains(["rhel", "win22", "sql", "win16"], var.os_flavor)
    error_message = "OS flavor must be one of: 'rhel', 'win22', 'sql', 'win16'."
  }
}

variable "size" {
  description = "The SKU size of the Virtual Machine."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "admin_username" {
  description = "The administrator username."
  type        = string
  default     = "azureadmin"
}

variable "admin_password" {
  description = "The administrator password (required for Windows, optional for Linux if SSH key provided)."
  type        = string
  sensitive   = true
  default     = null
}

variable "ssh_public_key" {
  description = "The SSH public key (required for Linux if password not provided)."
  type        = string
  default     = null
}

variable "data_disks" {
  description = "List of data disks to attach."
  type = list(object({
    name                 = optional(string)
    disk_size_gb         = number
    lun                  = number
    storage_account_type = optional(string, "Premium_LRS")
    caching              = optional(string, "ReadWrite")
    disk_iops_read_write = optional(number)
    disk_mbps_read_write = optional(number)
  }))
  default = []
}

variable "tags" {
  description = "A mapping of tags to assign to the resource."
  type        = map(string)
  default     = {}
}
