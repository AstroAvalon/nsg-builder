output "id" {
  description = "The ID of the Logic App Workflow."
  value       = azurerm_logic_app_workflow.workflow.id
}

output "principal_id" {
  description = "The Principal ID of the System Assigned Identity of the Logic App Workflow."
  value       = azurerm_logic_app_workflow.workflow.identity[0].principal_id
}

output "name" {
  description = "The name of the Logic App Workflow."
  value       = azurerm_logic_app_workflow.workflow.name
}
