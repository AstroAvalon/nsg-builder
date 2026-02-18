locals {
  # 1. Lock the order so AppDatabase doesn't steal index 0 from the Gateway
  subnet_order = ["GatewaySubnet", "AppWeb", "AppDatabase", "AppTools", "AppPrivateLink"]

  # 2. Map the data
  subnet_config = {
    GatewaySubnet  = { name = "GatewaySubnet",  has_nsg = false, service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppWeb         = { name = "AppWeb",         has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppDatabase    = { name = "AppDatabase",    has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppTools       = { name = "AppTools",       has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
    AppPrivateLink = { name = "AppPrivateLink", has_nsg = true,  service_endpoints = [], aks_delegation = false, databricks_delegation = false, postgres_delegation = false }
  }

  # 3. Calculate CIDRs (Indices 0=3, 1=4, 2=4, 3=4, 4=4)
  calculated_cidrs = cidrsubnets(var.project.address_space[0], 3, 4, 4, 4, 4)

  # 4. Map names to their calculated IPs
  subnet_with_cidr = {
    for i, key in local.subnet_order : key => local.calculated_cidrs[i]
  }

  subnet_rules = {
    "AppWeb"         = var.AppWeb_nsg_rules
    "AppDatabase"    = var.AppDatabase_nsg_rules
    "AppTools"       = var.AppTools_nsg_rules
    "AppPrivateLink" = []
    "GatewaySubnet"  = [] 
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
