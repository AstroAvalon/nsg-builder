variable "virtual_machines" {
  description = "Map of Virtual Machine configurations."
  type = map(object({
    role           = string
    instance       = string
    os_type        = string
    subnet_key     = string
    size           = optional(string, "Standard_D2s_v3")
    admin_username = optional(string, "azureadmin")
    admin_password = optional(string) # Required for Windows
    ssh_public_key = optional(string)
    data_disks     = optional(list(object({
      name                 = optional(string)
      disk_size_gb         = number
      lun                  = number
      storage_account_type = optional(string, "Premium_LRS")
      caching              = optional(string, "ReadWrite")
      disk_iops_read_write = optional(number)
      disk_mbps_read_write = optional(number)
    })), [])
  }))
  default = {}
}
