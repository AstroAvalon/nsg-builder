terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
      configuration_aliases = [ azurerm.management ]
    }
  }
}

resource "azurerm_storage_account" "account" {
  for_each = { for sa in var.storage_account_config : sa.name => sa }

  name                                = each.value.name
  resource_group_name                 = var.resource_group_name
  location                            = var.location
  account_kind                        = each.value.account_kind
  account_tier                        = each.value.account_tier
  account_replication_type            = each.value.account_replication_type
  access_tier                         = each.value.account_kind == "BlockBlobStorage" ? null : each.value.access_tier
  shared_access_key_enabled           = !each.value.disable_access_keys
  https_traffic_only_enabled          = each.value.enable_https_traffic_only
  is_hns_enabled                      = each.value.enable_hns != null ? each.value.enable_hns : false
  nfsv3_enabled                       = each.value.nfsv3_enabled != null ? each.value.nfsv3_enabled : false
  cross_tenant_replication_enabled    = each.value.enable_cross_tenant_replication != null ? each.value.enable_cross_tenant_replication : false
  public_network_access_enabled       = false
  allow_nested_items_to_be_public     = false
  infrastructure_encryption_enabled   = true

  network_rules {
    default_action = "Deny"
    bypass         = ["Logging", "Metrics", "AzureServices"]
  }

  dynamic "blob_properties" {
    for_each = contains(["StorageV2", "BlockBlobStorage"], each.value.account_kind) ? [1] : []
    content {
      delete_retention_policy {
        days = 7
      }
      container_delete_retention_policy {
        days = 7
      }
    }
  }

  tags = var.tags
}

locals {
  blob_containers = flatten([
    for sa in var.storage_account_config : [
      for container in sa.containers : {
        storage_account_name = sa.name
        container_name      = container
      }
      if (
        sa.account_kind == "BlockBlobStorage" ||
        (sa.account_kind == "StorageV2" && sa.account_tier != "Premium")
      )
    ]
  ])
}

resource "azurerm_storage_container" "blob_container" {
  for_each = {
    for bc in local.blob_containers :
    "${bc.storage_account_name}-${bc.container_name}" => bc
  }

  name               = each.value.container_name
  storage_account_id = azurerm_storage_account.account[each.value.storage_account_name].id
  container_access_type = "private"

  depends_on = [azurerm_storage_account.account]
}

locals {
  file_shares = flatten([
    for sa in var.storage_account_config : [
      for container in sa.containers : {
        storage_account_name = sa.name
        container_name      = container
      }
      if sa.account_kind == "FileStorage"
    ]
  ])
}

resource "azurerm_storage_share" "file_share" {
  for_each = {
    for fs in local.file_shares : 
    "${fs.storage_account_name}-${fs.container_name}" => fs
  }

  name                = each.value.container_name
  storage_account_id  = azurerm_storage_account.account[each.value.storage_account_name].id
  quota                = 5120
  enabled_protocol     = "NFS"

  depends_on = [ azurerm_storage_account.account ]

}

resource "azurerm_private_endpoint" "blob_pep" {
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_blob_endpoint }

  name                = "blob-pe-${each.value.name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "blob-psc-${each.value.name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_storage_account.account[each.key].id
    subresource_names              = ["blob"]
  }

  private_dns_zone_group {
    name                 = "blob-default"
    private_dns_zone_ids = var.blob_zone_id
  }
}

resource "azurerm_private_dns_a_record" "blob_a_record" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_blob_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.blob.core.windows.net"
  resource_group_name = var.blob_zone_rg_secondary
  ttl                 = 300
  records             = [azurerm_private_endpoint.blob_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_dns_a_record" "blob_a_record_tertiary" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_blob_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.blob.core.windows.net"
  resource_group_name = var.blob_zone_rg_tertiary
  ttl                 = 300
  records             = [azurerm_private_endpoint.blob_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_endpoint" "dfs_pep" {
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_dfs_endpoint }

  name                = "dfs-pe-${each.value.name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "dfs-psc-${each.value.name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_storage_account.account[each.key].id
    subresource_names              = ["dfs"]
  }

  private_dns_zone_group {
    name                 = "dfs-default"
    private_dns_zone_ids = var.dfs_zone_id
  }
}

resource "azurerm_private_dns_a_record" "dfs_a_record" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_dfs_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.dfs.core.windows.net"
  resource_group_name = var.dfs_zone_rg_secondary
  ttl                 = 300
  records             = [azurerm_private_endpoint.dfs_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_dns_a_record" "dfs_a_record_tertiary" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_dfs_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.dfs.core.windows.net"
  resource_group_name = var.dfs_zone_rg_tertiary
  ttl                 = 300
  records             = [azurerm_private_endpoint.dfs_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_endpoint" "file_pep" {
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_file_endpoint }

  name                = "file-pe-${each.value.name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "file-psc-${each.value.name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_storage_account.account[each.key].id
    subresource_names              = ["file"]
  }

  private_dns_zone_group {
    name                 = "file-default"
    private_dns_zone_ids = var.file_zone_id
  }
}

resource "azurerm_private_dns_a_record" "file_a_record" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_file_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.file.core.windows.net"
  resource_group_name = var.file_zone_rg_secondary
  ttl                 = 300
  records             = [azurerm_private_endpoint.file_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_dns_a_record" "file_a_record_tertiary" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_file_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.file.core.windows.net"
  resource_group_name = var.file_zone_rg_tertiary
  ttl                 = 300
  records             = [azurerm_private_endpoint.file_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_endpoint" "table_pep" {
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_table_endpoint }

  name                = "table-pe-${each.value.name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "table-psc-${each.value.name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_storage_account.account[each.key].id
    subresource_names              = ["table"]
  }

  private_dns_zone_group {
    name                 = "table-default"
    private_dns_zone_ids = var.table_zone_id
  }
}

resource "azurerm_private_dns_a_record" "table_a_record" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_table_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.table.core.windows.net"
  resource_group_name = var.table_zone_rg_secondary
  ttl                 = 300
  records             = [azurerm_private_endpoint.table_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_dns_a_record" "table_a_record_tertiary" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_table_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.table.core.windows.net"
  resource_group_name = var.table_zone_rg_tertiary
  ttl                 = 300
  records             = [azurerm_private_endpoint.table_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_endpoint" "queue_pep" {
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_queue_endpoint }

  name                = "queue-pe-${each.value.name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "queue-psc-${each.value.name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_storage_account.account[each.key].id
    subresource_names              = ["queue"]
  }

  private_dns_zone_group {
    name                 = "queue-default"
    private_dns_zone_ids = var.queue_zone_id
  }
}

resource "azurerm_private_dns_a_record" "queue_a_record" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_queue_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.queue.core.windows.net"
  resource_group_name = var.queue_zone_rg_secondary
  ttl                 = 300
  records             = [azurerm_private_endpoint.queue_pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_dns_a_record" "queue_a_record_tertiary" {
  provider = azurerm.management
  for_each = { for sa in var.storage_account_config : sa.name => sa if sa.create_queue_endpoint }

  name                = each.value.name
  zone_name           = "privatelink.queue.core.windows.net"
  resource_group_name = var.queue_zone_rg_tertiary
  ttl                 = 300
  records             = [azurerm_private_endpoint.queue_pep[each.key].private_service_connection[0].private_ip_address]
}
