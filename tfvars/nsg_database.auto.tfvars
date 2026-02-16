Database_nsg_rules = [
  # --- New Rules Added via Automation 2026-02-16 ---
  {
    name                       = "Database_IN_Allow1000"
    description                = "New file, starts at 1000 again"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.1.0/24"
    source_port_range          = "*"
    destination_address_prefix = "10.0.2.0/24"
    destination_port_range     = "1433"
  },
  {
    name                       = "Database_IN_Allow1010"
    description                = "Testing "Any" protocol and spacey commas"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "10.1.1.1"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "3306,3307"
  },
]
