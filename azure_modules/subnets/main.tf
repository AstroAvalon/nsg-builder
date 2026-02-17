# 1. Create the Subnet
resource "azurerm_subnet" "subnet" {
  name                 = var.subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.network_name
  address_prefixes     = [var.address_space]
}

# 2. Create the NSG (Only if a name is provided)
resource "azurerm_network_security_group" "nsg" {
  count = var.security_group_name != null ? 1 : 0

  name                = var.security_group_name
  location            = var.location
  resource_group_name = var.resource_group_name
}

# 3. Create the Rules inside the NSG
# Jules TO-DO - Right now, this only supports rules that explicitly use "source_port_range" "destination_port_range"
# "source_address_prefix" and "destination_address_prefix", but there are also "prefixes" and "ranges" provided by the API
# We need to analyze the input variable and using conditional rules, have TF determine which API parameter to pass
# This should be a dynamic block, and a simple/effective way to do this would be to use length/split to determine
# if there is one value in the range/port field or more than one, and send a null value for whichever one is not true
# and the input for whichever one is true.
resource "azurerm_network_security_rule" "rules" {
  for_each = var.security_group_name != null ? { for r in var.nsg_rules : r.name => r } : {}

  resource_group_name         = var.resource_group_name
  network_security_group_name = azurerm_network_security_group.nsg[0].name
  
  name                        = each.value.name
  priority                    = each.value.priority
  direction                   = each.value.direction
  access                      = each.value.access
  protocol                    = each.value.protocol
  source_port_range           = each.value.source_port_range
  destination_port_range      = each.value.destination_port_range
  source_address_prefix       = each.value.source_address_prefix
  destination_address_prefix  = each.value.destination_address_prefix
}

# 4. Associate NSG to Subnet
resource "azurerm_subnet_network_security_group_association" "assoc" {
  count = var.security_group_name != null ? 1 : 0

  subnet_id                 = azurerm_subnet.subnet.id
  network_security_group_id = azurerm_network_security_group.nsg[0].id
}