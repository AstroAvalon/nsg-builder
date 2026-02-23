# Root main.tf or versions.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9.0"
    }
  }

  # Backend configuration for Terraform State
  # This will be initialized with -backend-config parameters in the pipeline
  #backend "azurerm" {}
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

# Fetch current client configuration (Tenant ID, Object ID, etc.)
data "azurerm_client_config" "current" {}
