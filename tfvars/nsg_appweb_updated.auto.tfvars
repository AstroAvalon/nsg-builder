AppWeb_nsg_rules = [
  # --- New Rules Added via Automation 2026-02-16 ---
  {
    name                       = "AppWeb_IN_Allow1000"
    description                = "Fixes spaces and periods in ports"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.0.1,10.0.0.2"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "80,443"
  },
  {
    name                       = "AppWeb_IN_Allow1010"
    description                = "Fixes casing and auto-prioritizes"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "172.16.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "VirtualNetwork"
    destination_port_range     = "8080,8443"
  },
  {
    name                       = "AppWeb_OUT_Deny1000"
    description                = "Independent priority starting at 1000"
    priority                   = 1000
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "Udp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "Internet"
    destination_port_range     = "53,123"
  },
  {
    name                       = "AppWeb_IN_Allow2500"
    description                = "Respects manual priority if provided"
    priority                   = 2500
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "22"
  },
  # --- New Rules Added via Automation 2026-02-16 17:18 ---
  {
    name                       = "AppWeb_IN_Allow1020"
    description                = "Fixes spaces and periods in ports"
    priority                   = 1020
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.0.1,10.0.0.2"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "80,443"
  },
  {
    name                       = "AppWeb_IN_Allow1030"
    description                = "Fixes casing and auto-prioritizes"
    priority                   = 1030
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "172.16.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "VirtualNetwork"
    destination_port_range     = "8080,8443"
  },
  {
    name                       = "AppWeb_OUT_Deny1010"
    description                = "Independent priority starting at 1000"
    priority                   = 1010
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "Udp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "Internet"
    destination_port_range     = "53,123"
  },
  {
    name                       = "AppWeb_IN_Allow2500"
    description                = "Respects manual priority if provided"
    priority                   = 2500
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "22"
  },
]
