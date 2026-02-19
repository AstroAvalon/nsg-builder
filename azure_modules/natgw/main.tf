locals {
  natgw_name = "natgw-${var.base_resource_name}"
  pip_name   = "pip-${local.natgw_name}"
}

# 1. Public IP for NAT Gateway
resource "azurerm_public_ip" "nat_pip" {
  name                = local.pip_name
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = [var.project.availability_zone]

  tags = var.tags
}

# 2. NAT Gateway
resource "azurerm_nat_gateway" "natgw" {
  name                    = local.natgw_name
  location                = var.location
  resource_group_name     = var.resource_group_name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
  zones                   = [var.project.availability_zone]

  tags = var.tags
}

# 3. Associate Public IP with NAT Gateway
resource "azurerm_nat_gateway_public_ip_association" "natgw_pip_assoc" {
  nat_gateway_id       = azurerm_nat_gateway.natgw.id
  public_ip_address_id = azurerm_public_ip.nat_pip.id
}

# 4. Associate Subnets with NAT Gateway
resource "azurerm_subnet_nat_gateway_association" "subnet_assoc" {
  for_each       = var.subnet_ids
  subnet_id      = each.value
  nat_gateway_id = azurerm_nat_gateway.natgw.id
}
