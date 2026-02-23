resource "random_string" "backend_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_resource_group" "backend" {
  name     = "rg-terraform-backend-${var.project.environment_level}"
  location = var.region_codes[var.project.location]
  tags     = {
    Environment = var.project.environment_level
    Purpose     = "Terraform State Backend"
  }
}

resource "azurerm_storage_account" "backend" {
  name                     = "sttfbackend${random_string.backend_suffix.result}"
  resource_group_name      = azurerm_resource_group.backend.name
  location                 = azurerm_resource_group.backend.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true
  }

  tags = {
    Environment = var.project.environment_level
    Purpose     = "Terraform State Backend"
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id  = azurerm_storage_account.backend.id
  container_access_type = "private"
}

output "backend_storage_account_name" {
  value = azurerm_storage_account.backend.name
}

output "backend_resource_group_name" {
  value = azurerm_resource_group.backend.name
}

output "backend_container_name" {
  value = azurerm_storage_container.tfstate.name
}
