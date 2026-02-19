terraform {
  required_version = ">= 1.9.0" # v4 recommends a newer Terraform CLI

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
  }
}
