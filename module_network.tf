module "virtual_network" {
  source              = "./azure_modules/virtual_network"
  resource_group_name = module.resource_groups["network"].name
  location            = var.region_codes[var.project.location]
  vnet_name           = local.vnet_name
  address_space       = var.project.address_space

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}