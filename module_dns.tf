module "private_dns" {
  source = "./azure_modules/private_dns"

  resource_group_name = module.resource_groups["network"].name
  vnet_id             = module.virtual_network.id
  secondary_location  = local.secondary_location

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}
