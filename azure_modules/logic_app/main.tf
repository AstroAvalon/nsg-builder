terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }
  }
}

resource "azurerm_service_plan" "asp" {
  name                = var.app_service_plan_name
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Windows"
  sku_name            = "WS1"

  tags = var.tags
}

resource "azurerm_eventgrid_system_topic" "egst" {
  name                = "egst-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  source_resource_id  = azurerm_storage_account.sa.id
  topic_type          = "Microsoft.Storage.StorageAccounts"

  tags = var.tags
}

resource "azurerm_storage_account" "sa" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

resource "azurerm_storage_container" "reports" {
  name                  = "reports"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

resource "azurerm_logic_app_standard" "logic_app" {
  name                       = var.name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  app_service_plan_id        = azurerm_service_plan.asp.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key

  virtual_network_subnet_id = var.subnet_id_integration

  app_settings = var.app_settings

  site_config {
    dotnet_framework_version  = "v6.0"
    use_32_bit_worker_process = var.use_32_bit_worker_process
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "pep" {
  name                = "pep-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id_pe

  private_service_connection {
    name                           = "psc-${var.name}"
    private_connection_resource_id = azurerm_logic_app_standard.logic_app.id
    is_manual_connection           = false
    subresource_names              = ["sites"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = var.private_dns_zone_ids
  }

  tags = var.tags
}
