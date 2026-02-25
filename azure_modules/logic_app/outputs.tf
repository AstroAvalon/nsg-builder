output "id" {
  description = "The ID of the Logic App Standard."
  value       = azurerm_logic_app_standard.logic_app.id
}

output "principal_id" {
  description = "The Principal ID of the Logic App Managed Identity."
  value       = azurerm_logic_app_standard.logic_app.identity[0].principal_id
}

output "tenant_id" {
  description = "The Tenant ID of the Logic App Managed Identity."
  value       = azurerm_logic_app_standard.logic_app.identity[0].tenant_id
}

output "app_service_plan_id" {
  description = "The ID of the App Service Plan."
  value       = azurerm_service_plan.asp.id
}

output "storage_account_id" {
  description = "The ID of the Logic App Storage Account."
  value       = azurerm_storage_account.sa.id
}

output "storage_account_name" {
  description = "The Name of the Logic App Storage Account."
  value       = azurerm_storage_account.sa.name
}

output "private_endpoint_ip" {
  description = "The Private IP of the Logic App Private Endpoint."
  value       = azurerm_private_endpoint.pep.private_service_connection[0].private_ip_address
}
