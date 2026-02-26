terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_logic_app_workflow" "workflow" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_api_connection" "azureblob" {
  name                = "azureblob-connection"
  resource_group_name = var.resource_group_name
  managed_api_id      = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/providers/Microsoft.Web/locations/${replace(lower(var.location), " ", "")}/managedApis/azureblob"
  display_name        = "azureblob-connection"

  parameter_values = {
    accountName = var.storage_account_name
    accessKey   = var.storage_account_access_key
  }

  tags = var.tags
}

resource "azurerm_eventgrid_system_topic" "egst" {
  name                = "egst-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  source_resource_id  = var.storage_account_id
  topic_type          = "Microsoft.Storage.StorageAccounts"

  tags = var.tags
}
