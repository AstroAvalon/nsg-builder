module "automation_account" {
  source = "./azure_modules/automation_account"

  name                = "aa-${local.base_resource_name}-reporting"
  resource_group_name = module.resource_groups["reporting"].name
  location            = var.region_codes[var.project.location]

  subnet_id           = module.subnets["AppPrivateLink"].id
  private_dns_zone_ids = [module.private_dns.primary_zone_ids["privatelink.azure-automation.net"]]

  report_storage_account_id   = module.logic_app.storage_account_id
  report_storage_account_name = module.logic_app.storage_account_name

  runbooks = {
    "Generate-MonthlyReport" = {
      runbook_type = "PowerShell72"
      content      = file("${path.module}/scripts/generate_report.ps1")
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
  app_service_plan_name = "asp-${local.base_resource_name}-reporting"
  storage_account_name  = substr("st${replace(local.base_resource_name, "-", "")}rpt", 0, 24)

  resource_group_name   = module.resource_groups["reporting"].name
  location              = var.region_codes[var.project.location]

  subnet_id_integration = module.subnets["AppReporting"].id
  subnet_id_pe          = module.subnets["AppPrivateLink"].id

  # Logic App Standard uses blob/file/queue/table storage, but the PE for Logic App (sites) uses azurewebsites.net
  private_dns_zone_ids  = [module.private_dns.primary_zone_ids["privatelink.azurewebsites.net"]]

  use_32_bit_worker_process = false

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"                        = "dotnet"
  }

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
  }
}

# Grant Logic App access to read/write blobs in its storage account (where reports are)
resource "azurerm_role_assignment" "logic_app_storage" {
  scope                = module.logic_app.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.logic_app.principal_id
}

# Grant Logic App access to send emails via ACS
resource "azurerm_role_assignment" "logic_app_acs" {
  scope                = module.communication_service.id
  role_definition_name = "Contributor"
  principal_id         = module.logic_app.principal_id
}
