AppWeb_nsg_rules = [
  # --- New Rules Added via Automation 2026-02-17 15:57 ---
  {
    name                       = "AppWeb_IN_Allow1000"
    description                = "Allow HTTPS from Load Balancer/Internet"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "Internet"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.32/28"
    destination_port_range     = "443"
  },
  {
    name                       = "AppWeb_IN_Allow1010"
    description                = "Allow Azure Gateway Manager probes"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "GatewayManager"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.32/28"
    destination_port_range     = "443"
  },
  {
    name                       = "AppWeb_IN_Allow1020"
    description                = "Management access from AppTools"
    priority                   = 1020
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.200.69.64/28"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.32/28"
    destination_port_range     = "22,3389"
  },
]
