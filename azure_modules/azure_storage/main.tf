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

locals {
  service_types = ["blob", "file", "dfs", "queue", "table"]

  # Map service name to DNS zone name suffix
  dns_zone_names = {
    blob  = "privatelink.blob.core.windows.net"
    file  = "privatelink.file.core.windows.net"
    dfs   = "privatelink.dfs.core.windows.net"
    queue = "privatelink.queue.core.windows.net"
    table = "privatelink.table.core.windows.net"
  }

  # Flatten the configuration into a list of endpoints to create
  endpoints_list = flatten([
    for sa in var.storage_account_config : [
      for service in local.service_types : {
        key                  = "${sa.name}-${service}"
        storage_account_name = sa.name
        service_name         = service
      }
      if lookup(sa, "create_${service}_endpoint", false)
    ]
  ])

  # Convert list to map for for_each
  endpoints_map = {
    for ep in local.endpoints_list : ep.key => ep
  }
}

resource "azurerm_private_endpoint" "pep" {
  for_each = local.endpoints_map

  name                = "${each.value.service_name}-pe-${each.value.storage_account_name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "${each.value.service_name}-psc-${each.value.storage_account_name}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_storage_account.account[each.value.storage_account_name].id
    subresource_names              = [each.value.service_name]
  }

  private_dns_zone_group {
    name                 = "${each.value.service_name}-default"
    private_dns_zone_ids = var.dns_zones[each.value.service_name].ids
  }
}

resource "azurerm_private_dns_a_record" "secondary" {
  provider = azurerm.management
  for_each = local.endpoints_map

  name                = each.value.storage_account_name
  zone_name           = local.dns_zone_names[each.value.service_name]
  resource_group_name = var.dns_zones[each.value.service_name].secondary_rg
  ttl                 = 300
  records             = [azurerm_private_endpoint.pep[each.key].private_service_connection[0].private_ip_address]
}

resource "azurerm_private_dns_a_record" "tertiary" {
  provider = azurerm.management
  for_each = local.endpoints_map

  name                = each.value.storage_account_name
  zone_name           = local.dns_zone_names[each.value.service_name]
  resource_group_name = var.dns_zones[each.value.service_name].tertiary_rg
  ttl                 = 300
  records             = [azurerm_private_endpoint.pep[each.key].private_service_connection[0].private_ip_address]
}
