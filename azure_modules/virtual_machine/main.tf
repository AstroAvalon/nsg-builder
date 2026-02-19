locals {
  # Convert list of data disks to a map keyed by LUN for stable iteration
  data_disks_map = {
    for disk in var.data_disks : disk.lun => disk
  }

  image_config = {
    rhel = {
      os_type   = "linux"
      publisher = "RedHat"
      offer     = "RHEL"
      sku       = "8-lvm"
      version   = "latest"
    }
    win22 = {
      os_type   = "windows"
      publisher = "MicrosoftWindowsServer"
      offer     = "WindowsServer"
      sku       = "2022-Datacenter"
      version   = "latest"
    }
    sql = {
      os_type   = "windows"
      publisher = "MicrosoftSQLServer"
      offer     = "sql2022-ws2022"
      sku       = "sqldev"
      version   = "latest"
    }
    win16 = {
      os_type   = "windows"
      publisher = "MicrosoftWindowsServer"
      offer     = "WindowsServer"
      sku       = "2016-Datacenter"
      version   = "latest"
    }
  }
}

resource "azurerm_network_interface" "nic" {
  name                = "nic-${var.vm_name}"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
  }

  tags = var.tags
}

# --- Linux Virtual Machine ---
resource "azurerm_linux_virtual_machine" "vm" {
  count                           = local.image_config[var.image].os_type == "linux" ? 1 : 0
  name                            = var.vm_name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  size                            = var.size
  admin_username                  = var.admin_username
  admin_password                  = var.admin_password
  disable_password_authentication = var.ssh_public_key != null

  network_interface_ids = [
    azurerm_network_interface.nic.id,
  ]

  dynamic "admin_ssh_key" {
    for_each = var.ssh_public_key != null ? [1] : []
    content {
      username   = var.admin_username
      public_key = var.ssh_public_key
    }
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = local.image_config[var.image].publisher
    offer     = local.image_config[var.image].offer
    sku       = local.image_config[var.image].sku
    version   = local.image_config[var.image].version
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# --- Windows Virtual Machine ---
resource "azurerm_windows_virtual_machine" "vm" {
  count               = local.image_config[var.image].os_type == "windows" ? 1 : 0
  name                = var.vm_name
  computer_name       = var.vm_name # Max 15 chars enforced by variable validation
  resource_group_name = var.resource_group_name
  location            = var.location
  size                = var.size
  admin_username      = var.admin_username
  admin_password      = var.admin_password
  network_interface_ids = [
    azurerm_network_interface.nic.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = local.image_config[var.image].publisher
    offer     = local.image_config[var.image].offer
    sku       = local.image_config[var.image].sku
    version   = local.image_config[var.image].version
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# --- Data Disks ---
resource "azurerm_managed_disk" "data_disk" {
  for_each             = local.data_disks_map
  name                 = "${var.vm_name}-disk-${each.key}"
  location             = var.location
  resource_group_name  = var.resource_group_name
  storage_account_type = each.value.storage_account_type
  create_option        = "Empty"
  disk_size_gb         = each.value.disk_size_gb

  # Premium V2 specific settings
  disk_iops_read_write = each.value.storage_account_type == "PremiumV2_LRS" ? each.value.disk_iops_read_write : null
  disk_mbps_read_write = each.value.storage_account_type == "PremiumV2_LRS" ? each.value.disk_mbps_read_write : null

  tags = var.tags
}

resource "azurerm_virtual_machine_data_disk_attachment" "attachment" {
  for_each           = local.data_disks_map
  managed_disk_id    = azurerm_managed_disk.data_disk[each.key].id
  virtual_machine_id = try(azurerm_linux_virtual_machine.vm[0].id, azurerm_windows_virtual_machine.vm[0].id)
  lun                = each.key
  caching            = each.value.storage_account_type == "PremiumV2_LRS" ? "None" : each.value.caching
}
