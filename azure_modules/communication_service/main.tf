terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0.0"
    }
  }
}

resource "azurerm_email_communication_service" "ecs" {
  name                = var.email_service_name
  resource_group_name = var.resource_group_name
  data_location       = var.data_location
  tags                = var.tags
}

resource "azurerm_email_communication_service_domain" "domain" {
  name                     = var.domain_name
  email_service_id         = azurerm_email_communication_service.ecs.id
  domain_management        = "AzureManaged"

  tags = var.tags
}

resource "azurerm_communication_service" "acs" {
  name                = var.name
  resource_group_name = var.resource_group_name
  data_location       = var.data_location

  tags = var.tags
}

resource "azurerm_communication_service_email_domain_association" "association" {
  communication_service_id = azurerm_communication_service.acs.id
  email_service_domain_id  = azurerm_email_communication_service_domain.domain.id
}
