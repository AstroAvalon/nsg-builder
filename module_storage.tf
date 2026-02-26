
module "azure_storage" {
  source = "azure_modules/azure_storage"

  storage_account_config   = var.storage_account_config

  resource_group_name      = module.resource_groups["compute"].name
  resource_group_name_pep  = module.resource_groups["network"].name
  location                 = var.region_codes[var.project["location"]]
  subnet_id                = module.subnets["AppPrivateLink"].id

  dns_zones = {
    blob = {
      ids          = [module.private_dns.primary_zone_ids["privatelink.blob.core.windows.net"]]
      secondary_rg = "rg-${local.secondary_base_resource_name}-mgmt"
    }
    file = {
      ids          = [module.private_dns.primary_zone_ids["privatelink.file.core.windows.net"]]
      secondary_rg = "rg-${local.secondary_base_resource_name}-mgmt"
    }
    dfs = {
      ids          = [module.private_dns.primary_zone_ids["privatelink.dfs.core.windows.net"]]
      secondary_rg = "rg-${local.secondary_base_resource_name}-mgmt"
    }
    queue = {
      ids          = [module.private_dns.primary_zone_ids["privatelink.queue.core.windows.net"]]
      secondary_rg = "rg-${local.secondary_base_resource_name}-mgmt"
    }
    table = {
      ids          = [module.private_dns.primary_zone_ids["privatelink.table.core.windows.net"]]
      secondary_rg = "rg-${local.secondary_base_resource_name}-mgmt"
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
