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

  # New functionalities: Service Endpoints & Delegations
  service_endpoints     = try(each.value.service_endpoints, [])
  aks_delegation        = try(each.value.aks_delegation, false)
  databricks_delegation = try(each.value.databricks_delegation, false)
  postgres_delegation   = try(each.value.postgres_delegation, false)

  # Private Endpoint Network Policies is defaulted to "Enabled" in module variables,
  # but we can pass it explicitly if needed. Relying on default for now.

  depends_on = [ module.virtual_network ]
}
