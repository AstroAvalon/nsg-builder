output "id" {
  description = "The ID of the Virtual Machine."
  value       = try(azurerm_linux_virtual_machine.vm[0].id, azurerm_windows_virtual_machine.vm[0].id)
}

output "principal_id" {
  description = "The Principal ID of the System Assigned Identity."
  value       = try(azurerm_linux_virtual_machine.vm[0].identity[0].principal_id, azurerm_windows_virtual_machine.vm[0].identity[0].principal_id)
}

output "private_ip_address" {
  description = "The private IP address of the Virtual Machine."
  value       = azurerm_network_interface.nic.private_ip_address
}
