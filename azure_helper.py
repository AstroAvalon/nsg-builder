"""
Azure Helper Module for NSG Automation
Handles parsing of Terraform variables and interaction with Azure APIs (mock-friendly).

"""

import re
import os
import json
from typing import Dict, Optional, List, Tuple
from collections import namedtuple

# Define data structure for Azure Rule
AzureRule = namedtuple(
    "AzureRule",
    [
        "name",
        "priority",
        "direction",
        "access",
        "protocol",
        "source",
        "destination",
        "dest_port",
    ],
)


def parse_project_tfvars(filepath: str) -> Dict[str, str]:
    """
    Parses 'project.auto.tfvars' to extract project-level variables.
    Format: key = "value"
    """
    variables = {}
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: project.auto.tfvars not found at {filepath}")
        return variables

    with open(filepath, "r") as f:
        content = f.read()

    # Regex to capture simple key = "value" pairs
    matches = re.findall(r'(\w+)\s*=\s*"(.*?)"', content)
    for key, value in matches:
        variables[key] = value

    return variables


def parse_subnet_names_tf(filepath: str) -> Dict[str, str]:
    """
    Parses 'data_network_names.tf' to extract the 'subnet_names' map.
    Format:
    variable "subnet_names" {
      type = map(string)
      default = {
        "Key" = "Value"
      }
    }
    """
    subnets = {}
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: data_network_names.tf not found at {filepath}")
        return subnets

    with open(filepath, "r") as f:
        content = f.read()

    # Find the subnet_names block
    block_match = re.search(
        r'variable\s+"subnet_names"\s*\{.*?default\s*=\s*\{(.*?)\}\s*\}',
        content,
        re.DOTALL,
    )
    if block_match:
        inner_content = block_match.group(1)
        # Extract key-value pairs inside the map
        pairs = re.findall(r'"(.*?)"\s*=\s*"(.*?)"', inner_content)
        for key, value in pairs:
            subnets[key] = value

    return subnets


def get_resource_group_name(vars: Dict[str, str]) -> str:
    """
    Constructs Resource Group name: rg-{customer}-{client_code}-{location}-{environment_level}-network
    """
    required = ["customer", "client_code", "location", "environment_level"]
    missing = [k for k in required if k not in vars]
    if missing:
        raise ValueError(f"Missing required variables for RG construction: {missing}")

    return f"rg-{vars['customer']}-{vars['client_code']}-{vars['location']}-{vars['environment_level']}-network"


def get_nsg_name(subnet_name: str, env_level: str) -> str:
    """
    Constructs NSG name: NSG-{environment_level}-{subnet_name}
    """
    if not env_level:
        raise ValueError("Environment Level is required for NSG name construction")
    return f"NSG-{env_level}-{subnet_name}"


def fetch_azure_nsg_rules(
    resource_group: str, nsg_name: str, subscription_id: str = None
) -> List[AzureRule]:
    """
    Connects to Azure to fetch NSG rules.
    Mock-friendly: Uses try-import for Azure libraries.
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.network import NetworkManagementClient
    except ImportError:
        print("⚠️ Azure libraries not installed. Skipping live check.")
        return []

    try:
        credential = DefaultAzureCredential()
        # If subscription_id is not provided, use default from credential (if possible) or raise error
        # In a real scenario, subscription_id is crucial. Assuming it's passed or available in env.
        if not subscription_id:
            # Attempt to get subscription from environment variable if set, else explicit argument needed
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
            if not subscription_id:
                print("⚠️ No Subscription ID provided for Azure check.")
                return []

        network_client = NetworkManagementClient(credential, subscription_id)

        # Get NSG
        nsg = network_client.network_security_groups.get(resource_group, nsg_name)

        rules = []
        if nsg.security_rules:
            for rule in nsg.security_rules:
                # Filter Default Rules (Priority >= 65000)
                if rule.priority >= 65000:
                    continue

                # Create AzureRule object
                rules.append(
                    AzureRule(
                        name=rule.name,
                        priority=rule.priority,
                        direction=rule.direction,
                        access=rule.access,
                        protocol=rule.protocol,
                        source=rule.source_address_prefix,
                        destination=rule.destination_address_prefix,
                        dest_port=rule.destination_port_range,
                    )
                )
        return rules

    except Exception as e:
        print(f"❌ Azure API Error for {nsg_name}: {e}")
        return []
