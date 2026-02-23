AppDatabase_nsg_rules = [
  # Updated via Automation 2026-02-22 18:38
  {
    name                       = "AppDatabase_IN_Allow1000"
    description                = "Allow SQL from AppPrivateLink"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.1.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "1433"
  },
  {
    name                       = "AppDatabase_IN_Deny1010"
    description                = "Deny All Inbound Default"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
  {
    name                       = "AppDatabase_IN_Allow1030"
    description                = "Postgres Access"
    priority                   = 1030
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.2.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "5432"
  },
  {
    name                       = "AppDatabase_IN_Allow1040"
    description                = "MySQL Access"
    priority                   = 1040
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.3.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "3306"
  },
  {
    name                       = "AppDatabase_IN_Allow1069"
    description                = "Imported from Azure Drift"
    priority                   = 1069
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "8080"
  },
  {
    name                       = "AppDatabase_IN_Allow1510"
    description                = "Port Range with Dash"
    priority                   = 1510
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.20.20.20"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "8080-8090"
  },
  {
    name                       = "AppDatabase_OUT_Allow1020"
    description                = "Allow Azure Cloud Services"
    priority                   = 1020
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "AzureCloud"
    destination_port_range     = "443"
  },
]
