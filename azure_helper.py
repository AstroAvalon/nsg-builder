"""
Azure Helper Module for NSG Automation
Handles parsing of Terraform variables and interaction with Azure APIs (mock-friendly).

"""

import re
import os
import json
import subprocess
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
    Handles 'project = { ... }' block structure.
    """
    variables = {}
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: project.auto.tfvars not found at {filepath}")
        return variables

    with open(filepath, "r") as f:
        content = f.read()

    # Find the project block: project = { ... }
    # Using DOTALL to match across lines
    project_match = re.search(r"project\s*=\s*\{(.*?)\}", content, re.DOTALL)

    if project_match:
        inner_content = project_match.group(1)
        # Extract key-value pairs inside the block
        pairs = re.findall(r'(\w+)\s*=\s*"(.*?)"', inner_content)
        for key, value in pairs:
            variables[key] = value
    else:
        # Fallback for simple key="value" if project block not found (backward compat)
        matches = re.findall(r'(\w+)\s*=\s*"(.*?)"', content)
        for key, value in matches:
            variables[key] = value

    return variables


def parse_subnet_config(filepath: str) -> Dict[str, Dict]:
    """
    Parses 'locals.tf' to extract the 'subnet_config' map.
    Returns a dictionary of subnet configurations:
    {
        "SubnetKey": { "name": "Name", "has_nsg": True/False, ... }
    }
    """
    subnets = {}
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: locals.tf not found at {filepath}")
        return subnets

    with open(filepath, "r") as f:
        content = f.read()

    # Find the start of the subnet_config block
    start_match = re.search(r'subnet_config\s*=\s*\{', content)
    if not start_match:
        return subnets

    start_idx = start_match.end()
    inner_content = ""
    brace_count = 1  # We already found the opening brace

    # Iterate through remaining content to find the matching closing brace
    for char in content[start_idx:]:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1

        if brace_count == 0:
            break
        inner_content += char

    # Now parse the inner content
    # Parse each entry like: Key = { name = "Val", has_nsg = true/false, ... }
    entries = re.findall(r'(\w+)\s*=\s*\{(.*?)\}', inner_content, re.DOTALL)

    for key, props_str in entries:
        props = {}
        # Extract name
        name_match = re.search(r'name\s*=\s*"([^"]+)"', props_str)
        if name_match:
            props["name"] = name_match.group(1)

        # Extract has_nsg
        nsg_match = re.search(r'has_nsg\s*=\s*(true|false)', props_str)
        if nsg_match:
            props["has_nsg"] = nsg_match.group(1) == "true"
        else:
            props["has_nsg"] = False  # Default or fallback

        subnets[key] = props

    return subnets


def get_resource_group_name(vars: Dict[str, str]) -> str:
    """
    Constructs Resource Group name: rg-{customer}-{client_code}-{location}-{environment_level}-network
    Forces all components to lowercase.
    """
    required = ["customer", "client_code", "location", "environment_level"]
    missing = [k for k in required if k not in vars]
    if missing:
        raise ValueError(f"Missing required variables for RG construction: {missing}")

    return f"rg-{vars['customer'].lower()}-{vars['client_code'].lower()}-{vars['location'].lower()}-{vars['environment_level'].lower()}-network"


def get_nsg_name(subnet_name: str, env_level: str) -> str:
    """
    Constructs NSG name: NSG-{environment_level}-{subnet_name}
    Ensures environment level is uppercase.
    """
    if not env_level:
        raise ValueError("Environment Level is required for NSG name construction")
    return f"NSG-{env_level.upper()}-{subnet_name}"


def fetch_azure_nsg_rules(
    resource_group: str, nsg_name: str, subscription_id: str = None
) -> List[AzureRule]:
    """
    Connects to Azure to fetch NSG rules.
    Mock-friendly: Uses try-import for Azure libraries.
    """
    try:
        from azure.identity import AzureCliCredential
        from azure.mgmt.network import NetworkManagementClient
    except ImportError:
        print("⚠️ Azure libraries not installed. Skipping live check.")
        return []

    try:
        credential = AzureCliCredential()

        # If subscription_id is not provided, use default from credential (if possible) or raise error
        # In a real scenario, subscription_id is crucial. Assuming it's passed or available in env.
        if not subscription_id:
            # Attempt to get subscription from environment variable if set
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

            # If still missing, try to fetch from active az login session
            if not subscription_id:
                try:
                    result = subprocess.run(
                        ["az", "account", "show", "--query", "id", "-o", "tsv"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    subscription_id = result.stdout.strip()
                    print(f"ℹ️  Using active Azure Subscription: {subscription_id}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print(
                        "❌ Error: 'az' CLI not found or not logged in. Please run 'az login'."
                    )
                    return []

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
        if "CredentialUnavailableError" in str(type(e)) or "az login" in str(e).lower():
            print(
                "❌ Azure Authentication Failed. Please run 'az login' to authenticate."
            )
        else:
            print(f"❌ Azure API Error for {nsg_name}: {e}")
        return []
