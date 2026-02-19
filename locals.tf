locals {
  # 1. Lock the order so AppDatabase doesn't steal index 0 from the Gateway
  subnet_order = [
    "GatewaySubnet",
    "AppPrivateLink",
    "AppDatabase",
    "AppBudgetBooks",
    "AppTestSavvy",
    "AppMGMTTools",
    "AppReporting"
  ]

  # 2. Map the data
  subnet_config = {
    GatewaySubnet  = { name = "GatewaySubnet",  newbits = 3, netnum = 0,  has_nsg = false }
    AppPrivateLink = { name = "AppPrivateLink", newbits = 4, netnum = 2,  has_nsg = true  }
    AppDatabase    = { name = "AppDatabase",    newbits = 4, netnum = 4,  has_nsg = true  }
    AppBudgetBooks = { name = "AppBudgetBooks", newbits = 5, netnum = 12, has_nsg = true  }
    AppTestSavvy   = { name = "AppTestSavvy",   newbits = 4, netnum = 8,  has_nsg = true  }
    AppMGMTTools   = { name = "AppMGMTTools",   newbits = 4, netnum = 10, has_nsg = true  }
    AppReporting   = { name = "AppReporting",   newbits = 4, netnum = 12, has_nsg = true  }
  }

  # 3. Calculate CIDRs dynamically using newbits and netnum
  subnet_with_cidr = {
    for key, config in local.subnet_config : key => cidrsubnet(var.project.address_space[0], config.newbits, config.netnum)
  }

  subnet_rules = {
    "GatewaySubnet"  = []
    "AppPrivateLink" = var.AppPrivateLink_nsg_rules
    "AppDatabase"    = var.AppDatabase_nsg_rules
    "AppBudgetBooks" = var.AppBudgetBooks_nsg_rules
    "AppTestSavvy"   = var.AppTestSavvy_nsg_rules
    "AppMGMTTools"   = var.AppMGMTTools_nsg_rules
    "AppReporting"   = var.AppReporting_nsg_rules
  }

  # Base resource name: customer-client-loc-env (e.g., lab-astlab-wus-dr)
  base_resource_name = lower(join("-", [
    var.project.customer,
    var.project.client_code,
    var.project.location,
    var.project.environment_level
  ]))

  # Secondary Location (Paired Region)
  secondary_location_code = lookup(var.region_pairs, var.project.location, "EUS")
  secondary_location      = lookup(var.region_codes, local.secondary_location_code, "East US")

  # Map for resource groups (compute vs network)
  resource_group_names = {
    for type, suffix in var.resource_group_names : 
      type => suffix == "" ? "rg-${local.base_resource_name}" : "rg-${local.base_resource_name}-${suffix}"
  }

  # Virtual Network Name
  vnet_name = "vnet-${local.base_resource_name}"
}
