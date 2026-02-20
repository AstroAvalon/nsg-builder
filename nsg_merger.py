"""
Azure NSG Rule Merger

Parses an Excel sheet of firewall requests and merges them into Terraform variables (.tfvars).
Supports "Base Rules" for project initiation that apply to all subnets with dynamic CIDR replacement.
"""

import pandas as pd
import re
import os
import glob
import argparse
import sys
from datetime import datetime
from typing import Tuple, Dict, Optional, List, Set, Any

try:
    import azure_helper
except ImportError:
    print("Warning: azure_helper module not found. Azure integration disabled.")
    azure_helper = None

# Configuration
OUTPUT_SUFFIX = "_updated"
START_PRIORITY = 1000
PRIORITY_STEP = 10

# Pre-compiled Regexes
RE_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]")
RE_DOT_BETWEEN_NUMBERS = re.compile(r"(\d)\s*\.\s*(\d)")
RE_WHITESPACE = re.compile(r"\s+")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Merge NSG rules from Excel to Terraform files.")
    parser.add_argument("excel_file", nargs="?", help="Path to the Excel request file", default=None)
    parser.add_argument("--base-rules", help="Path to Base Rules Excel file (Applies to ALL subnets)", default=None)
    parser.add_argument("--repo-root", default=".", help="Root directory of the repo")
    return parser.parse_args()

def find_existing_file(subnet_name: str, valid_files: List[str]) -> Optional[str]:
    safe_name = RE_ALPHANUMERIC.sub("", str(subnet_name)).lower()
    for file_path in valid_files:
        filename = os.path.basename(file_path).lower()
        # Remove output suffix to match original files too
        clean_filename = filename.replace(OUTPUT_SUFFIX, "").replace("_", "").replace(".", "")
        if safe_name in clean_filename:
            return file_path
    return None

def format_rule(rule: Dict[str, Any]) -> str:
    order = [
        "name", "description", "priority", "direction", "access", "protocol",
        "source_address_prefix", "source_address_prefixes",
        "source_port_range", "source_port_ranges",
        "destination_address_prefix", "destination_address_prefixes",
        "destination_port_range", "destination_port_ranges"
    ]
    hcl = "  {\n"
    for key in order:
        if key in rule:
            val = rule[key]
            if isinstance(val, int):
                hcl += f'    {key:<26} = {val}\n'
            else:
                hcl += f'    {key:<26} = "{val}"\n'
    for key, val in rule.items():
        if key not in order:
             if isinstance(val, int):
                hcl += f'    {key:<26} = {val}\n'
             else:
                hcl += f'    {key:<26} = "{val}"\n'
    hcl += "  },"
    return hcl

def clean_port(val: str) -> str:
    if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
        return "*"
    cleaned = RE_DOT_BETWEEN_NUMBERS.sub(r"\1,\2", str(val))
    return RE_WHITESPACE.sub("", cleaned).replace(",,", ",").strip(",")

def clean_ip(val: str) -> str:
    if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
        return "*"
    return RE_WHITESPACE.sub("", str(val)).strip(",")

def merge_nsg_rules(excel_path: str, base_rules_path: str, repo_root: str):
    tfvars_dir = os.path.join(repo_root, "tfvars")
    if not os.path.exists(tfvars_dir):
        print(f"Error: Could not find 'tfvars' folder at: {tfvars_dir}")
        return

    # Load Project Configuration
    print("Loading project configuration...")
    project_vars_path = os.path.join(repo_root, "tfvars", "project.auto.tfvars")
    locals_tf_path = os.path.join(repo_root, "locals.tf")

    project_vars = azure_helper.parse_project_tfvars(project_vars_path) if azure_helper else {}
    subnet_config = azure_helper.parse_subnet_config(locals_tf_path) if azure_helper else {}

    # Get VNet CIDR for replacement
    vnet_cidr = "10.0.0.0/16" # Default fallback
    if project_vars.get('address_space'):
        vnet_cidr = project_vars['address_space'][0]

    # Load Excel Data
    if excel_path:
        try:
            df_client = pd.read_excel(excel_path, dtype=str)
            df_client.columns = df_client.columns.str.strip()
        except Exception as e:
            print(f"Error reading Client Excel: {e}")
            return
    else:
        df_client = pd.DataFrame(columns=[
            "Azure Subnet Name", "Priority", "Direction", "Access",
            "Source", "Destination", "Protocol", "Destination Port", "Description"
        ])

    df_base = None
    if base_rules_path:
        try:
            df_base = pd.read_excel(base_rules_path, dtype=str)
            df_base.columns = df_base.columns.str.strip()
            print(f"Base Rules Loaded: {len(df_base)} rules found.")
        except Exception as e:
            print(f"Error reading Base Rules Excel: {e}")
            return

    # Determine Target Subnets (Resolve Names to Keys)
    name_to_key = {}
    for k, v in subnet_config.items():
        if "name" in v:
            name_to_key[v["name"]] = k
        name_to_key[k] = k

    target_keys = set()

    # Process Client Excel Subnets
    raw_client_subnets = set(df_client["Azure Subnet Name"].dropna().unique())
    if "GatewaySubnet" in raw_client_subnets:
        raw_client_subnets.remove("GatewaySubnet")

    for s in raw_client_subnets:
        key = name_to_key.get(s, s)
        target_keys.add(key)

    # If Base Rules enabled, include ALL config subnets with has_nsg=true
    if df_base is not None:
        config_keys = {k for k, v in subnet_config.items() if v.get("has_nsg", False)}
        target_keys = target_keys.union(config_keys)
        print(f"Base Rules Enabled: Processing {len(target_keys)} subnets.")

    api_map = {
        "TCP": "Tcp", "UDP": "Udp", "ICMP": "Icmp", "ANY": "*", "*": "*",
        "INBOUND": "Inbound", "OUTBOUND": "Outbound",
        "ALLOW": "Allow", "DENY": "Deny"
    }

    all_files = glob.glob(os.path.join(tfvars_dir, "*.auto.tfvars"))
    valid_files = [f for f in all_files if OUTPUT_SUFFIX not in f]

    for subnet_key in target_keys:
        if str(subnet_key).lower() == "gatewaysubnet": continue
        print(f"\nProcessing Subnet: {subnet_key}")

        # Identify File
        existing_file = find_existing_file(subnet_key, valid_files)
        var_name = f"{RE_ALPHANUMERIC.sub('', str(subnet_key))}_nsg_rules"

        # Merging structure (Priority -> Rule Dict)
        merged_rules: Dict[int, Dict[str, Any]] = {}

        # Load Existing Rules
        existing_rules_list = []
        if existing_file:
            print(f"   Reading Source: {os.path.basename(existing_file)}")
            with open(existing_file, "r") as f:
                content = f.read()
                existing_rules_list = azure_helper.parse_hcl_rules(content)
                m_var = re.search(r"(\w+)\s*=", content)
                if m_var: var_name = m_var.group(1)

            for r in existing_rules_list:
                merged_rules[r['priority']] = r

            base_name = os.path.basename(existing_file)
            name_part, _ = os.path.splitext(base_name)
            name_part = name_part.replace(".auto", "")
            new_filename = os.path.join(tfvars_dir, f"{name_part}{OUTPUT_SUFFIX}.auto.tfvars")
        else:
            clean_name = RE_ALPHANUMERIC.sub("", str(subnet_key)).lower()
            new_filename = os.path.join(tfvars_dir, f"nsg_{clean_name}.auto.tfvars")
            print(f"   Creating NEW file: {os.path.basename(new_filename)}")

        # Track Used Priorities
        used_priorities_in = {r['priority'] for r in merged_rules.values() if "IN" in str(r.get('direction')).upper()}
        used_priorities_out = {r['priority'] for r in merged_rules.values() if "OUT" in str(r.get('direction')).upper()}
        prio_counters = {"IN": START_PRIORITY, "OUT": START_PRIORITY}

        # Azure Drift Check
        if azure_helper and project_vars:
             try:
                rg_name = azure_helper.get_resource_group_name(project_vars)
                tf_subnet_key_drift = subnet_key

                if subnet_config.get(tf_subnet_key_drift, {}).get("has_nsg", True):
                    nsg_name = azure_helper.get_nsg_name(tf_subnet_key_drift, project_vars.get("environment_level"))
                    sub_id = project_vars.get("customer_subscription_id")

                    print(f"   Querying Azure NSG: {nsg_name}")
                    azure_rules = azure_helper.fetch_azure_nsg_rules(rg_name, nsg_name, sub_id)

                    for az_rule in azure_rules:
                        is_inbound = "IN" in az_rule.direction.upper()
                        if az_rule.priority in merged_rules:
                            continue

                        print(f"   DRIFT: Found Priority {az_rule.priority} in Azure. Importing...")
                        rule_dict = {
                            "name": az_rule.name,
                            "description": "Imported from Azure Drift",
                            "priority": az_rule.priority,
                            "direction": az_rule.direction,
                            "access": az_rule.access,
                            "protocol": az_rule.protocol,
                            "source_address_prefix": az_rule.source,
                            "source_port_range": "*",
                            "destination_address_prefix": az_rule.destination,
                            "destination_port_range": az_rule.dest_port
                        }
                        merged_rules[az_rule.priority] = rule_dict
                        if is_inbound: used_priorities_in.add(az_rule.priority)
                        else: used_priorities_out.add(az_rule.priority)

             except Exception as e:
                 print(f"   Azure Check Warning: {e}")

        # Process Client Rules
        real_name = subnet_config.get(subnet_key, {}).get("name", subnet_key)
        client_rules_for_subnet = df_client[
            (df_client["Azure Subnet Name"] == subnet_key) |
            (df_client["Azure Subnet Name"] == real_name)
        ]

        for _, row in client_rules_for_subnet.iterrows():
            raw_dir = str(row["Direction"]).upper().strip()
            dir_short = "IN" if "IN" in raw_dir else "OUT"
            is_inbound = (dir_short == "IN")

            prio_val = None
            try:
                if not pd.isna(row["Priority"]) and str(row["Priority"]).strip() != "":
                    prio_val = int(float(row["Priority"]))
            except: pass

            if prio_val and prio_val in merged_rules:
                existing = merged_rules[prio_val]
                is_identical = True
                comparisons = [
                    ("direction", api_map.get(raw_dir, "Inbound")),
                    ("access", api_map.get(str(row["Access"]).upper().strip(), "Allow")),
                    ("protocol", api_map.get(str(row["Protocol"]).upper().strip(), "Tcp")),
                    ("source_address_prefix", clean_ip(row['Source'])),
                    ("destination_address_prefix", clean_ip(row['Destination'])),
                    ("destination_port_range", clean_port(row['Destination Port'])),
                    ("source_port_range", "*")
                ]

                for key, new_val in comparisons:
                    existing_val = existing.get(key)
                    if str(existing_val).strip().lower() != str(new_val).strip().lower():
                        is_identical = False
                        break

                if is_identical:
                    print(f"   Skipping Identical Rule at Priority {prio_val}")
                    continue
                else:
                    print(f"   Conflict at Priority {prio_val}. Assigning new priority.")
                    prio_val = None

            if not prio_val:
                target_set = used_priorities_in if is_inbound else used_priorities_out
                while prio_counters[dir_short] in target_set or prio_counters[dir_short] in merged_rules:
                    prio_counters[dir_short] += PRIORITY_STEP
                prio_val = prio_counters[dir_short]
                prio_counters[dir_short] += PRIORITY_STEP

            merged_rules[prio_val] = {
                "name": f"{RE_ALPHANUMERIC.sub('', str(subnet_key))}_{dir_short}_{api_map.get(str(row['Access']).upper().strip(), 'Allow')}{prio_val}",
                "description": str(row['Description'])[:100],
                "priority": prio_val,
                "direction": api_map.get(raw_dir, "Inbound"),
                "access": api_map.get(str(row["Access"]).upper().strip(), "Allow"),
                "protocol": api_map.get(str(row["Protocol"]).upper().strip(), "Tcp"),
                "source_address_prefix": clean_ip(row['Source']),
                "source_port_range": "*",
                "destination_address_prefix": clean_ip(row['Destination']),
                "destination_port_range": clean_port(row['Destination Port'])
            }
            if is_inbound: used_priorities_in.add(prio_val)
            else: used_priorities_out.add(prio_val)

        # Process Base Rules
        if df_base is not None:
            current_cidr = ""
            subnet_conf = subnet_config.get(subnet_key)
            if subnet_conf and azure_helper:
                current_cidr = azure_helper.calculate_subnet_cidr(
                    vnet_cidr, subnet_conf.get("newbits", 0), subnet_conf.get("netnum", 0)
                )

            if not current_cidr:
                print(f"   Warning: Could not calculate CIDR for {subnet_key}. {{CurrentSubnet}} will be invalid.")
                current_cidr = "ERROR_CIDR_CALC"

            for _, row in df_base.iterrows():
                raw_dir = str(row["Direction"]).upper().strip()
                dir_short = "IN" if "IN" in raw_dir else "OUT"

                try:
                    prio_val = int(float(row["Priority"]))
                except:
                    print(f"   Base Rule Error: Missing Priority. Skipping.")
                    continue

                src_clean = clean_ip(row['Source']).replace("{{CurrentSubnet}}", current_cidr).replace("{{VNetCIDR}}", vnet_cidr)
                dst_clean = clean_ip(row['Destination']).replace("{{CurrentSubnet}}", current_cidr).replace("{{VNetCIDR}}", vnet_cidr)

                if prio_val in merged_rules:
                    print(f"   Base Rule Overwriting Priority {prio_val}")

                merged_rules[prio_val] = {
                    "name": f"{RE_ALPHANUMERIC.sub('', str(subnet_key))}_{dir_short}_{api_map.get(str(row['Access']).upper().strip(), 'Allow')}{prio_val}",
                    "description": str(row['Description'])[:100],
                    "priority": prio_val,
                    "direction": api_map.get(raw_dir, "Inbound"),
                    "access": api_map.get(str(row["Access"]).upper().strip(), "Allow"),
                    "protocol": api_map.get(str(row["Protocol"]).upper().strip(), "Tcp"),
                    "source_address_prefix": src_clean,
                    "source_port_range": "*",
                    "destination_address_prefix": dst_clean,
                    "destination_port_range": clean_port(row['Destination Port'])
                }

        # Sort and Write
        final_list = list(merged_rules.values())
        final_list.sort(key=lambda r: (
            0 if "in" in str(r.get("direction")).lower() else 1,
            r.get("priority", 99999)
        ))

        print(f"   Writing {len(final_list)} rules...")
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)
        with open(new_filename, "w") as f:
            f.write(f"{var_name} = [\n")
            f.write(f"  # Updated via Automation {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            for rule in final_list:
                f.write(format_rule(rule) + "\n")
            f.write("]\n")

        print(f"   SUCCESS: Wrote to -> {new_filename}")

if __name__ == "__main__":
    args = parse_arguments()
    merge_nsg_rules(args.excel_file, args.base_rules, args.repo_root)
