module "private_dns" {
  source = "./azure_modules/private_dns"

  resource_group_name           = module.resource_groups["mgmt"].name
  secondary_resource_group_name = "rg-${local.secondary_base_resource_name}-mgmt"
  vnet_id                       = module.virtual_network.id
  secondary_location            = local.secondary_location

  dns_zone_names = [
    "privatelink.vaultcore.azure.net",
    "privatelink.blob.core.windows.net",
    "privatelink.table.core.windows.net",
    "privatelink.queue.core.windows.net",
    "privatelink.file.core.windows.net",
    "privatelink.azure-automation.net",
    "privatelink.azurewebsites.net",
    "privatelink.communication.azure.com"
  ]

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}
