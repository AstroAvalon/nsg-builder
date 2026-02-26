terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }
  }
}

data "azurerm_subscription" "current" {}

resource "azurerm_automation_account" "account" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = var.sku_name
  public_network_access_enabled = var.enable_public_network_access

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_automation_runbook" "runbook" {
  for_each = var.runbooks

  name                    = each.key
  location                = var.location
  resource_group_name     = var.resource_group_name
  automation_account_name = azurerm_automation_account.account.name
  log_verbose             = true
  log_progress            = true
  description             = each.value.description
  runbook_type            = each.value.runbook_type

  content = each.value.content

  tags = var.tags
}

resource "azurerm_automation_powershell72_module" "importexcel" {
  name                  = "ImportExcel"
  automation_account_id = azurerm_automation_account.account.id
  module_link {
    uri = "https://www.powershellgallery.com/api/v2/package/ImportExcel"
  }
}

resource "azurerm_automation_variable_string" "report_storage_account" {
  name                    = "ReportStorageAccountName"
  resource_group_name     = var.resource_group_name
  automation_account_name = azurerm_automation_account.account.name
  value                   = var.report_storage_account_name
}

resource "azurerm_role_assignment" "reader" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Reader"
  principal_id         = azurerm_automation_account.account.identity[0].principal_id
}

resource "azurerm_role_assignment" "storage_contributor" {
  scope                = var.report_storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_automation_account.account.identity[0].principal_id
}

resource "azurerm_private_endpoint" "pep" {
  name                = "pep-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-${var.name}"
    private_connection_resource_id = azurerm_automation_account.account.id
    is_manual_connection           = false
    subresource_names              = ["Webhook"] # Used for Webhooks and Runbook execution
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = var.private_dns_zone_ids
  }

  tags = var.tags
}
