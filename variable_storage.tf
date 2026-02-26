variable "storage_account_config" {
  description = "List of storage accounts to create"
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
    public_network_access_enabled = optional(bool, false)
  }))
  default = []
}
