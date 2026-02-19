locals {
  # Map environment levels to single character
  env_char_map = {
    PRD  = "p"
    NPRD = "n"
    DR   = "d"
  }
  # Fallback logic: If not in map, take first letter of lower-cased env level
  env_char = lookup(local.env_char_map, var.project.environment_level, substr(lower(var.project.environment_level), 0, 1))

  # Map location to single character (e.g., WUS -> w, EUS -> e)
  region_char = substr(lower(var.project.location), 0, 1)
}

module "virtual_machines" {
  source = "./azure_modules/virtual_machine"

  for_each = var.virtual_machines

  # Naming logic: vm-{role}-{env}-{region}-{instance}
  # Max 15 chars: 2+1+3+1+1+1+1+1+2 = 13
  vm_name = "vm-${each.value.role}-${local.env_char}-${local.region_char}-${each.value.instance}"

  resource_group_name = module.resource_groups["compute"].name
  location            = var.region_codes[var.project.location]

  # Ensure the subnet key exists in the subnet module outputs
  subnet_id           = module.subnets[each.value.subnet_key].id

  os_type        = each.value.os_type
  size           = each.value.size
  admin_username = each.value.admin_username
  admin_password = each.value.admin_password
  ssh_public_key = each.value.ssh_public_key
  data_disks     = each.value.data_disks

  tags = {
    Environment = var.project.environment_level
    Client      = var.project.client_code
    Role        = each.value.role
  }
}
