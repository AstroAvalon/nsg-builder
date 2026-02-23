AppPrivateLink_nsg_rules = [
  # Updated via Automation 2026-02-22 18:04
  {
    name                       = "AppPrivateLink_IN_Allow1000"
    description                = "Allow HTTPS"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "443"
  },
  {
    name                       = "AppPrivateLink_IN_Allow1010"
    description                = "Internal HTTP"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.0.0/8"
    source_port_range          = "*"
    destination_address_prefix = "10.1.0.0/24"
    destination_port_range     = "80"
  },
  {
    name                       = "AppPrivateLink_IN_Deny1020"
    description                = "Block UDP"
    priority                   = 1020
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Udp"
    source_address_prefix      = "0.0.0.0/0"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
  {
    name                       = "AppPrivateLink_IN_Allow1040"
    description                = "SSH Access from Bastion"
    priority                   = 1040
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "192.168.1.1,192.168.1.2"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "22"
  },
  {
    name                       = "AppPrivateLink_IN_Allow1500"
    description                = "Comma Separated Ports"
    priority                   = 1500
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.10.10.10"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "80,443"
  },
  {
    name                       = "AppPrivateLink_OUT_Allow1030"
    description                = "Outbound Internet HTTPS"
    priority                   = 1030
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "Internet"
    destination_port_range     = "443"
  },
]
