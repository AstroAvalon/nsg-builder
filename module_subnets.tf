module "subnets" {
  source   = "./azure_modules/subnets"
  for_each = local.subnet_config

  resource_group_name = module.resource_groups["network"].name
  location            = var.region_codes[var.project.location]
  network_name        = local.vnet_name
  subnet_name         = each.value.name
  security_group_name = each.value.has_nsg ? "NSG-${upper(var.project.environment_level)}-${each.value.name}" : null
  nsg_rules           = local.subnet_rules[each.key]
  address_space       = local.calculated_cidrs[index(local.subnet_keys_ordered, each.key)]
}