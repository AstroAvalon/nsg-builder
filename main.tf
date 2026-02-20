# Root main.tf or versions.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id     = var.project["customer_subscription_id"]
  storage_use_azuread = true
}

provider "azurerm" {
  features {}
  alias               = "management"
  subscription_id     = var.project["customer_subscription_id"] # utilizing same sub for now, user to update if different
  storage_use_azuread = true
}
