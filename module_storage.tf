module "azure_storage" {
  source = "azure_modules/azure_storage"

  storage_account_config   = var.storage_account_config

  resource_group_name      = module.resource_group["compute"].name
  resource_group_name_pep  = module.resource_group["network"].name
  location                 = var.region_codes[var.project["location"]]
  subnet_id                = module.AppPrivateLink.subnet.subnet_id
  blob_zone_id             = [data.azurerm_private_dns_zone.blob_zone_wus.id]
  file_zone_id             = [data.azurerm_private_dns_zone.file_zone_wus.id]
  dfs_zone_id              = [data.azurerm_private_dns_zone.dfs_zone_wus.id]
  table_zone_id            = [data.azurerm_private_dns_zone.table_zone_wus.id]
  queue_zone_id            = [data.azurerm_private_dns_zone.queue_zone_wus.id]

  blob_zone_rg_secondary   = data.azurerm_private_dns_zone.blob_zone_scus.resource_group_name
  file_zone_rg_secondary   = data.azurerm_private_dns_zone.file_zone_scus.resource_group_name
  dfs_zone_rg_secondary    = data.azurerm_private_dns_zone.dfs_zone_scus.resource_group_name
  table_zone_rg_secondary  = data.azurerm_private_dns_zone.table_zone_scus.resource_group_name
  queue_zone_rg_secondary  = data.azurerm_private_dns_zone.queue_zone_scus.resource_group_name
  
  providers = {
    azurerm = azurerm
    azurerm.management = azurerm.management
  }
}
