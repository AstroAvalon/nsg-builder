resource "azurerm_recovery_services_vault" "this" {
  name                          = var.vault_name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  sku                           = "Standard"
  storage_mode_type             = "LocallyRedundant"
  public_network_access_enabled = false

  tags = var.tags
}

resource "azurerm_backup_policy_vm" "daily" {
  name                = "${var.vault_name}-daily-policy"
  resource_group_name = var.resource_group_name
  recovery_vault_name = azurerm_recovery_services_vault.this.name

  backup {
    frequency = "Daily"
    time      = var.backup_time
  }

  retention_daily {
    count = 31
  }
}

resource "azurerm_backup_policy_vm" "enhanced" {
  name                = "${var.vault_name}-enhanced-policy"
  resource_group_name = var.resource_group_name
  recovery_vault_name = azurerm_recovery_services_vault.this.name
  policy_type         = "V2"

  backup {
    frequency = "Daily"
    time      = var.backup_time
  }

  retention_daily {
    count = 31
  }
}

resource "azurerm_private_endpoint" "this" {
  name                = "pe-${var.vault_name}"
  location            = var.location
  resource_group_name = var.resource_group_name_pep
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-${var.vault_name}"
    private_connection_resource_id = azurerm_recovery_services_vault.this.id
    is_manual_connection           = false
    subresource_names              = ["AzureBackup"]
  }

  private_dns_zone_group {
    name                 = "pdzg-${var.vault_name}"
    private_dns_zone_ids = [var.rv_zone_id]
  }

  tags = var.tags
}

resource "azurerm_private_dns_a_record" "secondary_record" {
  name                = var.vault_name
  zone_name           = split("/", var.rv_zone_id_secondary)[8]
  resource_group_name = split("/", var.rv_zone_id_secondary)[4]
  ttl                 = 300
  records             = [azurerm_private_endpoint.this.private_service_connection[0].private_ip_address]

  tags = var.tags
}
