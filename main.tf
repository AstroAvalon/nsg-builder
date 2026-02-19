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