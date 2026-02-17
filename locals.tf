locals {
  # 1. THE BLUEPRINT: Define names and NSG status in one combined map
  subnet_config = {
    GatewaySubnet  = { name = "GatewaySubnet",  has_nsg = false, newbits = 3 } # /27
    AppWeb         = { name = "AppWeb",         has_nsg = true,  newbits = 4 } # /28
    AppDatabase    = { name = "AppDatabase",    has_nsg = true,  max_nsg = 4 } # /28
    AppTools       = { name = "AppTools",       has_nsg = true,  newbits = 4 } # /28
    AppPrivateLink = { name = "AppPrivateLink", has_nsg = true,  newbits = 4 } # /28
  }

  # 2. CIDR SLICING: Create the CIDRs based on the order above
  # We use the keys from subnet_config to keep the order stable.
  subnet_keys_ordered = keys(local.subnet_config)
  
  # This slices the /24 into one /27 and four /28s
  calculated_cidrs = cidrsubnets(var.project.address_space[0], 3, 4, 4, 4, 4)

  # 3. RULE MAPPING: Map your variables to the keys
  subnet_rules = {
      "AppWeb"         = var.AppWeb_nsg_rules
      "AppDatabase"    = var.AppDatabase_nsg_rules
      "AppTools"       = var.AppTools_nsg_rules
      "AppPrivateLink" = []
      "GatewaySubnet"  = [] 
  }

  # Base naming convention: customer-client-loc-env (e.g., lab-astlab-wus-dr)
  base_rg_name = lower(join("-", [
    var.project.customer,
    var.project.client_code,
    var.project.location,
    var.project.environment_level
  ]))

  # Map for resource groups (compute vs network)
  resource_group_names = {
    for type, suffix in var.resource_group_names : 
      type => suffix == "" ? local.base_rg_name : "${local.base_rg_name}-${suffix}"
  }

  # Virtual Network Name
  vnet_name = "${local.base_rg_name}-vnet"
}