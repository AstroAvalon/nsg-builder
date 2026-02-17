module "resource_groups" {
  source = "./azure_modules/resource_groups" # Update this path to your actual module location

  # Iterate through the map: 
  # Key = "compute", Value = "lab-astlab-wus-dr"
  # Key = "network", Value = "lab-astlab-wus-dr-network"
  for_each = local.resource_group_names

  # Input Variables
  resource_group_name = each.value
  location            = var.region_codes[var.project["location"]]
  
  # For Jule: Create a tags variable uncomment this eventually
  # tags = var.tags 
}