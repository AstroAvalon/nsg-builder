output "id" {
  description = "The ID of the Automation Account."
  value       = azurerm_automation_account.account.id
}

output "name" {
  description = "The name of the Automation Account."
  value       = azurerm_automation_account.account.name
}

output "identity" {
  description = "The Managed Identity configuration of the Automation Account."
  value       = azurerm_automation_account.account.identity
}

output "private_endpoint_ip" {
  description = "The Private IP of the Private Endpoint."
  value       = azurerm_private_endpoint.pep.private_service_connection[0].private_ip_address
}

output "source_control_id" {
  description = "The ID of the Automation Source Control."
  value       = azurerm_automation_source_control.sc-repo.id
}
