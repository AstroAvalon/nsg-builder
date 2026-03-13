module "automation_account" {
  source = "./azure_modules/automation_account"

  name                = "aa-${local.base_resource_name}-reporting"
  resource_group_name = module.resource_groups["reporting"].name
  location            = var.region_codes[var.project.location]

  subnet_id           = module.subnets["AppPrivateLink"].id
  private_dns_zone_ids = [module.private_dns.primary_zone_ids["privatelink.azure-automation.net"]]

  report_storage_account_id   = module.azure_storage.storage_accounts["stlabastrowus3nprdrpt"].id
  report_storage_account_name = module.azure_storage.storage_accounts["stlabastrowus3nprdrpt"].name

  # Source Control Integration parameters
  devops_pat     = "dummy_pat_value"
  repository_url = "https://dev.azure.com/dummy/dummyrepo/_git/dummyrepo"
  branch         = "main"
  folder_path    = "scripts"

  runbooks = {
    "Generate-MonthlyReport" = {
      runbook_type = "PowerShell72"
      description  = "Generates monthly usage and cost report."
    }
  }

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}

module "communication_service" {
  source = "./azure_modules/communication_service"

  name                = "acs-${local.base_resource_name}"
  email_service_name  = "ecs-${local.base_resource_name}"
  domain_name         = "AzureManagedDomain"

  resource_group_name = module.resource_groups["reporting"].name
  location            = var.region_codes[var.project.location] # For PE
  data_location       = "United States" # ACS data location

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}

module "logic_app" {
  source = "./azure_modules/logic_app"

  name                  = "logic-${local.base_resource_name}-reporting"
  resource_group_name   = module.resource_groups["reporting"].name
  location              = var.region_codes[var.project.location]

  storage_account_name       = module.azure_storage.storage_accounts["stlabastrowus3nprdrpt"].name
  storage_account_access_key = module.azure_storage.storage_accounts["stlabastrowus3nprdrpt"].primary_access_key
  storage_account_id         = module.azure_storage.storage_accounts["stlabastrowus3nprdrpt"].id

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}

# Grant Logic App access to read/write blobs in its storage account (where reports are)
resource "azurerm_role_assignment" "logic_app_storage" {
  scope                = module.azure_storage.storage_accounts["stlabastrowus3nprdrpt"].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.logic_app.principal_id
}

# Grant Logic App access to send emails via ACS
resource "azurerm_role_assignment" "logic_app_acs" {
  scope                = module.communication_service.id
  role_definition_name = "Contributor"
  principal_id         = module.logic_app.principal_id
}
