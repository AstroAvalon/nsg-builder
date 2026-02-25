# Data source for the Primary Private DNS Zone (Backup)
data "azurerm_private_dns_zone" "backup_primary" {
  provider            = azurerm.management
  name                = "privatelink.backup.windowsazure.com"
  resource_group_name = module.resource_groups["mgmt"].name
}

# Data source for the Secondary Private DNS Zone (Backup)
data "azurerm_private_dns_zone" "backup_secondary" {
  provider            = azurerm.management
  name                = "privatelink.backup.windowsazure.com"
  resource_group_name = "rg-${local.secondary_base_resource_name}-mgmt"
}

module "recovery_services_vault" {
  source = "./azure_modules/recovery_services_vault"

  vault_name              = "rsv-${local.base_resource_name}"
  location                = var.region_codes[var.project.location]
  resource_group_name     = module.resource_groups["compute"].name
  resource_group_name_pep = module.resource_groups["network"].name
  subnet_id               = module.subnets["AppPrivateLink"].id
  rv_zone_id              = data.azurerm_private_dns_zone.backup_primary.id
  rv_zone_id_secondary    = data.azurerm_private_dns_zone.backup_secondary.id

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}
