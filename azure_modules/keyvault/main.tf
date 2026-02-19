locals {
  kv_name = "kv-${var.base_resource_name}"
  # Use the provided PE resource group name, or default to the main resource group name
  pe_resource_group_name = coalesce(var.pe_resource_group_name, var.resource_group_name)
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                        = local.kv_name
  location                    = var.location
  resource_group_name         = var.resource_group_name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"
  public_network_access_enabled = false

  rbac_authorization_enabled  = true

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }

  tags = var.tags
}

# Create Private Endpoint for Key Vault
resource "azurerm_private_endpoint" "pe" {
  name                = "pe-${local.kv_name}"
  location            = var.location
  resource_group_name = local.pe_resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-${local.kv_name}"
    private_connection_resource_id = azurerm_key_vault.kv.id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdzg-${local.kv_name}"
    private_dns_zone_ids = [var.private_dns_zone_ids["primary"]]
  }

  tags = var.tags
}

# Add DNS A-Record to the SECONDARY Private DNS Zone
# This satisfies the requirement: "create a PEP for the primary zone and also add a DNS record to the secondary dns zone"
# We extract the Resource Group Name and Zone Name from the provided secondary Zone ID.
# Private DNS Zone ID format: /subscriptions/{guid}/resourceGroups/{rg}/providers/Microsoft.Network/privateDnsZones/{name}
# split("/", id) results in:
# 0: ""
# 1: "subscriptions"
# 2: "{guid}"
# 3: "resourceGroups"
# 4: "{rg}"
# ...
# 8: "{name}"

resource "azurerm_private_dns_a_record" "secondary_record" {
  name                = local.kv_name
  zone_name           = split("/", var.private_dns_zone_ids["secondary"])[8]
  resource_group_name = split("/", var.private_dns_zone_ids["secondary"])[4]
  ttl                 = 300
  records             = [azurerm_private_endpoint.pe.private_service_connection[0].private_ip_address]

  tags = var.tags
}
