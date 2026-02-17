module "subnets" {
  source   = "./azure_modules/subnets"
  for_each = local.subnet_config

  resource_group_name = module.resource_groups["network"].name
  location            = var.region_codes[var.project.location]
  network_name        = local.vnet_name
  
  subnet_name         = each.value.name
  security_group_name = each.value.has_nsg ? "NSG-${upper(var.project.environment_level)}-${each.value.name}" : null
  nsg_rules           = local.subnet_rules[each.key]

  # Pulling from the ordered map we built in step 4 above
  address_space       = local.subnet_with_cidr[each.key]

  depends_on = [ module.virtual_network ]
}