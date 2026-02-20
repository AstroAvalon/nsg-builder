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

variable "blob_zone_id" {
  description = "The ID of the blob zone"
  type        = list(string)
}

variable "file_zone_id" {
  description = "The ID of the file zone"
  type        = list(string)
}

variable "dfs_zone_id" {
  description = "The ID of the dfs zone"
  type        = list(string)
}

variable "queue_zone_id" {
  description = "The ID of the queue zone"
  type        = list(string)
}

variable "table_zone_id" {
  description = "The ID of the table zone"
  type        = list(string)
}

variable "blob_zone_rg_secondary" {
  type = string
}

variable "dfs_zone_rg_secondary" {
  type = string
}

variable "file_zone_rg_secondary" {
  type = string
}

variable "queue_zone_rg_secondary" {
  type = string
}

variable "table_zone_rg_secondary" {
  type = string
}

variable "blob_zone_rg_tertiary" {
  type = string
}

variable "dfs_zone_rg_tertiary" {
  type = string
}

variable "file_zone_rg_tertiary" {
  type = string
}

variable "queue_zone_rg_tertiary" {
  type = string
}

variable "table_zone_rg_tertiary" {
  type = string
}
