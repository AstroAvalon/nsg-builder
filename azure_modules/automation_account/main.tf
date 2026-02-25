terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }
  }
}

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
