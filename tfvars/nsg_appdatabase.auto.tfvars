AppDatabase_nsg_rules = [
  # --- New Rules Added via Automation 2026-02-17 17:25 ---
  {
    name                       = "AppDatabase_IN_Allow1000"
    description                = "SQL Access from AppWeb tier"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.200.69.32/28"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.48/28"
    destination_port_range     = "1433"
  },
  {
    name                       = "AppDatabase_IN_Deny1010"
    description                = "Explicitly block direct access to DB"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.48/28"
    destination_port_range     = "*"
  },
]
