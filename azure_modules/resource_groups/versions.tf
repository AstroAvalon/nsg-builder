terraform {
  required_version = ">= 1.9.0" # v4 recommends a newer Terraform CLI

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      # This allows any 4.x version (e.g., 4.1, 4.20) but stops at 5.0
      version = ">= 4.0.0, < 5.0.0"
    }
  }
}