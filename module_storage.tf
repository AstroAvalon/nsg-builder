locals {
  # DNS Zone Resource Groups
  dns_rg_wus3 = "rg-${var.project.customer}-${var.project.client_code}-wus3-${var.project.environment_level}-mgmt"
  dns_rg_scus = "rg-${var.project.customer}-${var.project.client_code}-scus-${var.project.environment_level}-mgmt"
  dns_rg_eus  = "rg-${var.project.customer}-${var.project.client_code}-eus-${var.project.environment_level}-mgmt"
}

# --- Blob ---
data "azurerm_private_dns_zone" "blob_wus3" {
  provider            = azurerm.management
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = local.dns_rg_wus3
}
data "azurerm_private_dns_zone" "blob_scus" {
  provider            = azurerm.management
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = local.dns_rg_scus
}
data "azurerm_private_dns_zone" "blob_eus" {
  provider            = azurerm.management
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = local.dns_rg_eus
}

# --- File ---
data "azurerm_private_dns_zone" "file_wus3" {
  provider            = azurerm.management
  name                = "privatelink.file.core.windows.net"
  resource_group_name = local.dns_rg_wus3
}
data "azurerm_private_dns_zone" "file_scus" {
  provider            = azurerm.management
  name                = "privatelink.file.core.windows.net"
  resource_group_name = local.dns_rg_scus
}
data "azurerm_private_dns_zone" "file_eus" {
  provider            = azurerm.management
  name                = "privatelink.file.core.windows.net"
  resource_group_name = local.dns_rg_eus
}

# --- DFS ---
data "azurerm_private_dns_zone" "dfs_wus3" {
  provider            = azurerm.management
  name                = "privatelink.dfs.core.windows.net"
  resource_group_name = local.dns_rg_wus3
}
data "azurerm_private_dns_zone" "dfs_scus" {
  provider            = azurerm.management
  name                = "privatelink.dfs.core.windows.net"
  resource_group_name = local.dns_rg_scus
}
data "azurerm_private_dns_zone" "dfs_eus" {
  provider            = azurerm.management
  name                = "privatelink.dfs.core.windows.net"
  resource_group_name = local.dns_rg_eus
}

# --- Queue ---
data "azurerm_private_dns_zone" "queue_wus3" {
  provider            = azurerm.management
  name                = "privatelink.queue.core.windows.net"
  resource_group_name = local.dns_rg_wus3
}
data "azurerm_private_dns_zone" "queue_scus" {
  provider            = azurerm.management
  name                = "privatelink.queue.core.windows.net"
  resource_group_name = local.dns_rg_scus
}
data "azurerm_private_dns_zone" "queue_eus" {
  provider            = azurerm.management
  name                = "privatelink.queue.core.windows.net"
  resource_group_name = local.dns_rg_eus
}

# --- Table ---
data "azurerm_private_dns_zone" "table_wus3" {
  provider            = azurerm.management
  name                = "privatelink.table.core.windows.net"
  resource_group_name = local.dns_rg_wus3
}
data "azurerm_private_dns_zone" "table_scus" {
  provider            = azurerm.management
  name                = "privatelink.table.core.windows.net"
  resource_group_name = local.dns_rg_scus
}
data "azurerm_private_dns_zone" "table_eus" {
  provider            = azurerm.management
  name                = "privatelink.table.core.windows.net"
  resource_group_name = local.dns_rg_eus
}

module "azure_storage" {
  source = "azure_modules/azure_storage"

  storage_account_config   = var.storage_account_config

  resource_group_name      = module.resource_groups["compute"].name
  resource_group_name_pep  = module.resource_groups["network"].name
  location                 = var.region_codes[var.project["location"]]
  subnet_id                = module.subnets["AppPrivateLink"].id

  dns_zones = {
    blob = {
      ids          = [data.azurerm_private_dns_zone.blob_wus3.id]
      secondary_rg = data.azurerm_private_dns_zone.blob_scus.resource_group_name
      tertiary_rg  = data.azurerm_private_dns_zone.blob_eus.resource_group_name
    }
    file = {
      ids          = [data.azurerm_private_dns_zone.file_wus3.id]
      secondary_rg = data.azurerm_private_dns_zone.file_scus.resource_group_name
      tertiary_rg  = data.azurerm_private_dns_zone.file_eus.resource_group_name
    }
    dfs = {
      ids          = [data.azurerm_private_dns_zone.dfs_wus3.id]
      secondary_rg = data.azurerm_private_dns_zone.dfs_scus.resource_group_name
      tertiary_rg  = data.azurerm_private_dns_zone.dfs_eus.resource_group_name
    }
    queue = {
      ids          = [data.azurerm_private_dns_zone.queue_wus3.id]
      secondary_rg = data.azurerm_private_dns_zone.queue_scus.resource_group_name
      tertiary_rg  = data.azurerm_private_dns_zone.queue_eus.resource_group_name
    }
    table = {
      ids          = [data.azurerm_private_dns_zone.table_wus3.id]
      secondary_rg = data.azurerm_private_dns_zone.table_scus.resource_group_name
      tertiary_rg  = data.azurerm_private_dns_zone.table_eus.resource_group_name
    }
  }

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }

  providers = {
    azurerm = azurerm
    azurerm.management = azurerm.management
  }
}
