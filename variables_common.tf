variable "resource_group_names" {
  description = "A map defining the resource groups to create. The value is the suffix appended to the project base name (e.g., 'network'). If empty, the base name is used."
  type        = map(string)
  default = {
    compute = ""
    network = "network"
    mgmt    = "mgmt"
  }
}

variable "project" {
  description = "Project configuration details including subscription, location, and networking."
  type = object({
    customer_subscription_id = string
    location                 = string
    environment_level        = string
    customer                 = string
    client_code              = string
    availability_zone        = string
    address_space            = list(string)
  })
}

variable "region_codes" {
  description = "Map of internal short codes to Azure fully qualified region names."
  type        = map(string)
  default = {
    # East US
    EUS  = "East US"
    EUS2 = "East US 2"

    # West US
    WUS  = "West US"
    WUS2 = "West US 2"
    WUS3 = "West US 3"
    
    # Central US
    SCUS = "South Central US"
    CUS  = "Central US"
    NCUS = "North Central US"
    WCUS = "West Central US"
  }
}

variable "region_pairs" {
  description = "Map of primary regions to their paired secondary region."
  type        = map(string)
  default = {
    # West US <-> East US
    WUS  = "EUS"
    EUS  = "WUS"

    # West US 2 <-> West Central US
    WUS2 = "WCUS"
    WCUS = "WUS2"

    # West US 3 <-> East US
    WUS3 = "EUS"

    # Central US <-> East US 2
    CUS  = "EUS2"
    EUS2 = "CUS"

    # North Central US <-> South Central US
    NCUS = "SCUS"
    SCUS = "NCUS"
  }
}
