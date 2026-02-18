AppPrivateLink_nsg_rules = [
  # --- New Rules Added via Automation 2026-02-17 17:25 ---
  {
    name                       = "AppPrivateLink_IN_Allow1000"
    description                = "Private Endpoint access from Web tier"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.200.69.32/28"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.80/28"
    destination_port_range     = "443"
  },
]
