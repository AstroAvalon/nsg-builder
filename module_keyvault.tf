module "keyvault" {
  source = "./azure_modules/keyvault"

  project              = var.project
  resource_group_name  = module.resource_groups["compute"].name
  pe_resource_group_name = module.resource_groups["network"].name
  location             = var.region_codes[var.project.location]
  base_resource_name   = local.base_resource_name
  subnet_id            = module.subnets["AppPrivateLink"].id

  private_dns_zone_ids = {
    primary   = module.private_dns.primary_zone_ids["privatelink.vaultcore.azure.net"]
    secondary = module.private_dns.secondary_zone_ids["privatelink.vaultcore.azure.net"]
  }

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}
