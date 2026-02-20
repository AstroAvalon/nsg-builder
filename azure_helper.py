"""
Azure Helper Module for NSG Automation
Handles parsing of Terraform variables and interaction with Azure APIs (mock-friendly).

"""

import re
import os
import json
import subprocess
import ipaddress
from typing import Dict, Optional, List, Tuple, Any
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

# --- PRE-COMPILED REGEXES FOR HCL PARSING ---
RE_RULE_BLOCK = re.compile(r"\{\s*(.*?)\s*\}", re.DOTALL)
RE_KV_STRING = re.compile(r'(\w+)\s*=\s*"(.*?)"')
RE_KV_INT = re.compile(r'(\w+)\s*=\s*(\d+)')

def parse_project_tfvars(filepath: str) -> Dict[str, Any]:
    """
    Parses 'project.auto.tfvars' to extract project-level variables.
    Handles 'project = { ... }' block structure and lists like address_space.
    """
    variables = {}
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: project.auto.tfvars not found at {filepath}")
        return variables

    with open(filepath, "r") as f:
        content = f.read()

    # Find the project block: project = { ... }
    project_match = re.search(r"project\s*=\s*\{(.*?)\}", content, re.DOTALL)

    if project_match:
        inner_content = project_match.group(1)

        # 1. Extract List Values: key = ["val1", "val2"]
        # We handle this first to avoid partial string matching later
        list_matches = re.finditer(r'(\w+)\s*=\s*\[(.*?)\]', inner_content, re.DOTALL)
        for match in list_matches:
            key = match.group(1)
            raw_list_content = match.group(2)
            # Extract quoted strings from the list content
            items = re.findall(r'"(.*?)"', raw_list_content)
            variables[key] = items

        # 2. Extract String Values: key = "value"
        # We iterate again, but might overwrite list keys if not careful.
        # Simple regex strategy: find string pairs
        string_matches = re.findall(r'(\w+)\s*=\s*"(.*?)"', inner_content)
        for key, value in string_matches:
            # Only add if not already present (lists take precedence in this simple parser)
            if key not in variables:
                variables[key] = value

    return variables


def parse_subnet_config(filepath: str) -> Dict[str, Dict]:
    """
    Parses 'locals.tf' to extract the 'subnet_config' map.
    Returns a dictionary of subnet configurations:
    {
        "SubnetKey": { "name": "Name", "has_nsg": True/False, "newbits": int, "netnum": int }
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
            props["has_nsg"] = False

        # Extract newbits
        nb_match = re.search(r'newbits\s*=\s*(\d+)', props_str)
        if nb_match:
            props["newbits"] = int(nb_match.group(1))

        # Extract netnum
        nn_match = re.search(r'netnum\s*=\s*(\d+)', props_str)
        if nn_match:
            props["netnum"] = int(nn_match.group(1))

        subnets[key] = props

    return subnets


def calculate_subnet_cidr(base_cidr: str, newbits: int, netnum: int) -> str:
    """
    Calculates a specific subnet CIDR given the VNet base CIDR, newbits, and netnum.
    Simulates Terraform's cidrsubnet(prefix, newbits, netnum).
    """
    try:
        network = ipaddress.ip_network(base_cidr)
        # Generate all subnets with the new prefix length
        new_prefix = network.prefixlen + newbits
        subnets = list(network.subnets(new_prefix=new_prefix))

        if 0 <= netnum < len(subnets):
            return str(subnets[netnum])
        else:
            print(f"❌ Error: netnum {netnum} out of range for base {base_cidr} with newbits {newbits}")
            return ""
    except Exception as e:
        print(f"❌ Error calculating CIDR: {e}")
        return ""


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


def parse_hcl_rules(content: str) -> List[Dict[str, Any]]:
    """
    Parses a Terraform list of maps (HCL) into a list of Python dictionaries.
    Regex-based parsing to avoid requiring HCL library.
    """
    rules = []
    # Find list content: var = [ ... ]
    list_match = re.search(r"=\s*\[(.*)\]", content, re.DOTALL)
    if not list_match:
        return rules

    inner_content = list_match.group(1)

    # Iterate through each rule block { ... }
    for match in RE_RULE_BLOCK.finditer(inner_content):
        block_body = match.group(1)
        rule = {}
        # Parse Strings
        for kv in RE_KV_STRING.finditer(block_body):
            rule[kv.group(1)] = kv.group(2)
        # Parse Integers
        for kv in RE_KV_INT.finditer(block_body):
            rule[kv.group(1)] = int(kv.group(2))

        if rule:
            rules.append(rule)

    return rules


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
        if not subscription_id:
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
            if not subscription_id:
                try:
                    result = subprocess.run(
                        ["az", "account", "show", "--query", "id", "-o", "tsv"],
                        capture_output=True, text=True, check=True,
                    )
                    subscription_id = result.stdout.strip()
                    print(f"ℹ️  Using active Azure Subscription: {subscription_id}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("❌ Error: 'az' CLI not found or not logged in.")
                    return []

        if not subscription_id:
            print("⚠️ No Subscription ID provided for Azure check.")
            return []

        network_client = NetworkManagementClient(credential, subscription_id)
        nsg = network_client.network_security_groups.get(resource_group, nsg_name)

        rules = []
        if nsg.security_rules:
            for rule in nsg.security_rules:
                if rule.priority >= 65000: continue
                rules.append(AzureRule(
                    name=rule.name, priority=rule.priority, direction=rule.direction,
                    access=rule.access, protocol=rule.protocol,
                    source=rule.source_address_prefix, destination=rule.destination_address_prefix,
                    dest_port=rule.destination_port_range,
                ))
        return rules

    except Exception as e:
        if "CredentialUnavailableError" in str(type(e)) or "az login" in str(e).lower():
            print("❌ Azure Authentication Failed. Please run 'az login' to authenticate.")
        else:
            print(f"❌ Azure API Error for {nsg_name}: {e}")
        return []
