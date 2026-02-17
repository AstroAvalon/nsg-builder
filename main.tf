# Root main.tf or versions.tf
provider "azurerm" {
  features {}
  subscription_id     = var.project["customer_subscription_id"]
  storage_use_azuread = true
}