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
    GatewaySubnet  = { name = "GatewaySubnet",  newbits = 3, netnum = 0,  has_nsg = false, service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppPrivateLink = { name = "AppPrivateLink", newbits = 4, netnum = 2,  has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppDatabase    = { name = "AppDatabase",    newbits = 4, netnum = 4,  has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppBudgetBooks = { name = "AppBudgetBooks", newbits = 5, netnum = 12, has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppTestSavvy   = { name = "AppTestSavvy",   newbits = 4, netnum = 8,  has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppMGMTTools   = { name = "AppMGMTTools",   newbits = 4, netnum = 10, has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppReporting   = { name = "AppReporting",   newbits = 4, netnum = 12, has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
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

  # Base naming convention: customer-client-loc-env (e.g., lab-astlab-wus-dr)
  base_rg_name = lower(join("-", [
    "rg",
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

  vnet_name = lower(join("-", [
    "vnet",
    var.project.customer,
    var.project.client_code,
    var.project.location,
    var.project.environment_level
  ]))
}
