locals {
  # List of Private DNS Zones to create
  dns_zones = toset([
    "privatelink.vaultcore.azure.net",
    "privatelink.blob.core.windows.net",
    "privatelink.table.core.windows.net",
    "privatelink.queue.core.windows.net",
    "privatelink.file.core.windows.net"
  ])
}

# 1. Create Private DNS Zones (Primary)
resource "azurerm_private_dns_zone" "primary" {
  for_each            = local.dns_zones
  name                = each.value
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# 2. Link Primary Zones to VNet
resource "azurerm_private_dns_zone_virtual_network_link" "primary_link" {
  for_each              = local.dns_zones
  name                  = "link-primary-${replace(each.value, ".", "-")}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.primary[each.key].name
  virtual_network_id    = var.vnet_id
  registration_enabled  = false
}

# 3. Create Resource Group for Secondary Zones
# We create a new resource group for the secondary zones to allow duplicate zone names (since they are in different RGs)
# Note: Private DNS Zones are global resources, but they live in a resource group.
resource "azurerm_resource_group" "secondary" {
  name     = "${var.resource_group_name}-secondary-dns"
  location = var.secondary_location
  tags     = var.tags
}

# 4. Create Private DNS Zones (Secondary)
resource "azurerm_private_dns_zone" "secondary" {
  for_each            = local.dns_zones
  name                = each.value
  resource_group_name = azurerm_resource_group.secondary.name
  tags                = var.tags
}
