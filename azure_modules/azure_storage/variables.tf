variable "storage_account_config" {
  description = "List of storage accounts"
  type = list(object({
    name = string
    account_kind = string
    account_tier = string
    account_replication_type = string
    access_tier = string 
    enable_https_traffic_only = bool
    enable_cross_tenant_replication = bool
    disable_access_keys = bool
    nfsv3_enabled = bool
    create_blob_endpoint = bool
    create_file_endpoint = bool
    create_dfs_endpoint = bool
    create_table_endpoint = bool
    create_queue_endpoint = bool
    enable_hns = bool
    containers = list(string)
  }))
}

variable "resource_group_name" {
  type = string
}

variable "resource_group_name_pep" {
  type = string
}

variable "location" {
  type = string
}

variable "tags" {
  type = map
}

variable subnet_id {
  type = string
}

variable "dns_zones" {
  description = "Map of DNS zone configurations for each service (blob, file, dfs, queue, table)"
  type = map(object({
    ids           = list(string)
    secondary_rg  = string
    tertiary_rg   = string
  }))
}
