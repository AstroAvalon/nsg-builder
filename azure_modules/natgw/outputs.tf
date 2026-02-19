output "id" {
  description = "The ID of the NAT Gateway."
  value       = azurerm_nat_gateway.natgw.id
}

output "public_ip_address" {
  description = "The public IP address associated with the NAT Gateway."
  value       = azurerm_public_ip.nat_pip.ip_address
}
