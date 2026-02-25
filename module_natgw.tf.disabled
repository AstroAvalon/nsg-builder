module "natgw" {
  source = "./azure_modules/natgw"

  project              = var.project
  resource_group_name  = module.resource_groups["network"].name
  location             = var.region_codes[var.project.location]
  base_resource_name   = local.base_resource_name

  # Filter out subnets that should not have NAT Gateway attached (e.g., GatewaySubnet)
  subnet_ids = {
    for k, v in module.subnets : k => v.id
    if k != "GatewaySubnet" && k != "AzureFirewallSubnet"
  }

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}
