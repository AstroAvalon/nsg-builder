"""
MODULE: Azure NSG Rule Merger
VERSION: 2.2 (Subnet Resolution Fix)
AUTHOR: DevOps Team (Refactored by Jules)
DATE: 2026-02-19

DESCRIPTION:
  Parses an Excel sheet of firewall requests and merges them into Terraform variables (.tfvars).
  Supports "Base Rules" for project initiation that apply to all subnets with dynamic
  CIDR replacement.

  KEY FEATURES:
  - Client Request Merging (Safe Mode: Avoids Collisions).
  - Base Rules Merging (Project Init Mode: Overwrites Collisions).
  - Dynamic Placeholder Replacement: {{CurrentSubnet}}, {{VNetCIDR}}.
  - Azure Drift Detection.
  - Robust Subnet Name Resolution (Maps Excel Names to Terraform Config Keys).

ARCHITECTURAL CONSTRAINTS:
  1. Source of Truth: The existing .auto.tfvars files in the repo.
  2. Naming Convention: "{Subnet}_{In/Out}_{Allow/Deny}{Priority}".
"""

import pandas as pd
import re
import os
import glob
import argparse
import sys
from datetime import datetime
from typing import Tuple, Dict, Optional, List, Set, Any

# Import Azure Helper
try:
    import azure_helper
except ImportError:
    print("⚠️ Warning: azure_helper module not found. Azure integration disabled.")
    azure_helper = None

# --- CONFIGURATION ---
OUTPUT_SUFFIX = "_updated"
START_PRIORITY = 1000
PRIORITY_STEP = 10

# --- PRE-COMPILED REGEXES ---
RE_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]")
RE_DOT_BETWEEN_NUMBERS = re.compile(r"(\d)\s*\.\s*(\d)")
RE_WHITESPACE = re.compile(r"\s+")
RE_RULE_BLOCK = re.compile(r"\{\s*(.*?)\s*\}", re.DOTALL)
RE_KV_STRING = re.compile(r'(\w+)\s*=\s*"(.*?)"')
RE_KV_INT = re.compile(r'(\w+)\s*=\s*(\d+)')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Merge NSG rules from Excel to Terraform files.")
    parser.add_argument("excel_file", help="Path to the Excel request file")
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

def parse_hcl_rules(content: str) -> List[Dict[str, Any]]:
    rules = []
    list_match = re.search(r"=\s*\[(.*)\]", content, re.DOTALL)
    if not list_match:
        return rules

    inner_content = list_match.group(1)
    for match in RE_RULE_BLOCK.finditer(inner_content):
        block_body = match.group(1)
        rule = {}
        for kv in RE_KV_STRING.finditer(block_body):
            rule[kv.group(1)] = kv.group(2)
        for kv in RE_KV_INT.finditer(block_body):
            rule[kv.group(1)] = int(kv.group(2))
        if rule:
            rules.append(rule)
    return rules

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
        print(f"❌ Error: Could not find 'tfvars' folder at: {tfvars_dir}")
        return

    # --- Load Context ---
    print("ℹ️ Loading Project Configuration...")
    project_vars_path = os.path.join(repo_root, "tfvars", "project.auto.tfvars")
    locals_tf_path = os.path.join(repo_root, "locals.tf")

    project_vars = azure_helper.parse_project_tfvars(project_vars_path) if azure_helper else {}
    subnet_config = azure_helper.parse_subnet_config(locals_tf_path) if azure_helper else {}

    # Get VNet CIDR for {{VNetCIDR}} replacement
    vnet_cidr = "10.0.0.0/16" # Default fallback
    if project_vars.get('address_space'):
        vnet_cidr = project_vars['address_space'][0]

    # --- Load Excel Data ---
    try:
        df_client = pd.read_excel(excel_path, dtype=str)
        df_client.columns = df_client.columns.str.strip()
    except Exception as e:
        print(f"❌ Error reading Client Excel: {e}")
        return

    df_base = None
    if base_rules_path:
        try:
            df_base = pd.read_excel(base_rules_path, dtype=str)
            df_base.columns = df_base.columns.str.strip()
            print(f"ℹ️ Base Rules Loaded: {len(df_base)} rules found.")
        except Exception as e:
            print(f"❌ Error reading Base Rules Excel: {e}")
            return

    # --- Determine Target Subnets (Resolve Names to Keys) ---

    # Build Map: RealName -> Key
    name_to_key = {}
    for k, v in subnet_config.items():
        if "name" in v:
            name_to_key[v["name"]] = k
        name_to_key[k] = k # Ensure Key maps to itself

    target_keys = set()

    # 1. Process Client Excel Subnets
    raw_client_subnets = set(df_client["Azure Subnet Name"].dropna().unique())
    if "GatewaySubnet" in raw_client_subnets:
        raw_client_subnets.remove("GatewaySubnet")

    for s in raw_client_subnets:
        # Resolve to Key
        key = name_to_key.get(s, s) # Fallback to original if not found
        target_keys.add(key)

    # 2. If Base Rules enabled, include ALL config subnets with has_nsg=true
    if df_base is not None:
        config_keys = {k for k, v in subnet_config.items() if v.get("has_nsg", False)}
        target_keys = target_keys.union(config_keys)
        print(f"ℹ️ Base Rules Enabled: Processing {len(target_keys)} subnets.")

    # API Maps
    api_map = {
        "TCP": "Tcp", "UDP": "Udp", "ICMP": "Icmp", "ANY": "*", "*": "*",
        "INBOUND": "Inbound", "OUTBOUND": "Outbound",
        "ALLOW": "Allow", "DENY": "Deny"
    }

    all_files = glob.glob(os.path.join(tfvars_dir, "*.auto.tfvars"))
    valid_files = [f for f in all_files if OUTPUT_SUFFIX not in f]

    # --- MAIN LOOP ---
    for subnet_key in target_keys:
        if str(subnet_key).lower() == "gatewaysubnet": continue
        print(f"\nProcessing Subnet: {subnet_key}")

        # 1. Identify File
        existing_file = find_existing_file(subnet_key, valid_files)
        var_name = f"{RE_ALPHANUMERIC.sub('', str(subnet_key))}_nsg_rules"

        # Mapping: Priority -> Rule Dict
        # This is the core merging structure. Last write wins.
        merged_rules: Dict[int, Dict[str, Any]] = {}

        # 2. Load Existing Rules
        existing_rules_list = []
        if existing_file:
            print(f"   ↪ Reading Source: {os.path.basename(existing_file)}")
            with open(existing_file, "r") as f:
                content = f.read()
                existing_rules_list = parse_hcl_rules(content)
                m_var = re.search(r"(\w+)\s*=", content)
                if m_var: var_name = m_var.group(1)

            # Populate Map
            for r in existing_rules_list:
                merged_rules[r['priority']] = r

            base_name = os.path.basename(existing_file)
            name_part, _ = os.path.splitext(base_name)
            name_part = name_part.replace(".auto", "")
            new_filename = os.path.join(tfvars_dir, f"{name_part}{OUTPUT_SUFFIX}.auto.tfvars")
        else:
            clean_name = RE_ALPHANUMERIC.sub("", str(subnet_key)).lower()
            new_filename = os.path.join(tfvars_dir, f"nsg_{clean_name}.auto.tfvars")
            print(f"   ↪ Creating NEW file: {os.path.basename(new_filename)}")

        # Track Used Priorities
        used_priorities_in = {r['priority'] for r in merged_rules.values() if "IN" in str(r.get('direction')).upper()}
        used_priorities_out = {r['priority'] for r in merged_rules.values() if "OUT" in str(r.get('direction')).upper()}
        prio_counters = {"IN": START_PRIORITY, "OUT": START_PRIORITY}

        # 3. Azure Drift (Only if configured)
        if azure_helper and project_vars:
             try:
                rg_name = azure_helper.get_resource_group_name(project_vars)
                tf_subnet_key_drift = subnet_key

                # Check for NSG existence using config
                if subnet_config.get(tf_subnet_key_drift, {}).get("has_nsg", True):
                    nsg_name = azure_helper.get_nsg_name(tf_subnet_key_drift, project_vars.get("environment_level"))
                    sub_id = project_vars.get("customer_subscription_id")

                    print(f"   🔍 Querying Azure NSG: {nsg_name}")
                    azure_rules = azure_helper.fetch_azure_nsg_rules(rg_name, nsg_name, sub_id)

                    for az_rule in azure_rules:
                        is_inbound = "IN" in az_rule.direction.upper()
                        if az_rule.priority in merged_rules:
                            continue

                        print(f"   ⚠️  DRIFT: Found Priority {az_rule.priority} in Azure. Importing...")
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
                 print(f"   ❌ Azure Check Warning: {e}")

        # 4. Process Client Rules (Safe Merge)
        # Filter: Match Key OR RealName
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

            if prio_val:
                if prio_val in merged_rules:
                     print(f"   ⚠️ Client Rule Conflict: Priority {prio_val} already exists. Skipping Client Rule.")
                     continue
            else:
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

        # 5. Process Base Rules (Overwrite Mode)
        if df_base is not None:
            # Calculate CIDR using KEY
            current_cidr = ""
            subnet_conf = subnet_config.get(subnet_key)
            if subnet_conf and azure_helper:
                current_cidr = azure_helper.calculate_subnet_cidr(
                    vnet_cidr, subnet_conf.get("newbits", 0), subnet_conf.get("netnum", 0)
                )

            if not current_cidr:
                print(f"   ⚠️ Warning: Could not calculate CIDR for {subnet_key}. {{CurrentSubnet}} will be invalid.")
                current_cidr = "ERROR_CIDR_CALC"

            for _, row in df_base.iterrows():
                raw_dir = str(row["Direction"]).upper().strip()
                dir_short = "IN" if "IN" in raw_dir else "OUT"

                try:
                    prio_val = int(float(row["Priority"]))
                except:
                    print(f"   ❌ Base Rule Error: Missing Priority. Skipping.")
                    continue

                src_clean = clean_ip(row['Source']).replace("{{CurrentSubnet}}", current_cidr).replace("{{VNetCIDR}}", vnet_cidr)
                dst_clean = clean_ip(row['Destination']).replace("{{CurrentSubnet}}", current_cidr).replace("{{VNetCIDR}}", vnet_cidr)

                if prio_val in merged_rules:
                    print(f"   ℹ️  Base Rule Overwriting Priority {prio_val}")

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

        # 6. Sort and Write
        final_list = list(merged_rules.values())
        final_list.sort(key=lambda r: (
            0 if "in" in str(r.get("direction")).lower() else 1,
            r.get("priority", 99999)
        ))

        print(f"   ↪ Writing {len(final_list)} rules...")
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)
        with open(new_filename, "w") as f:
            f.write(f"{var_name} = [\n")
            f.write(f"  # --- Updated via Automation {datetime.now().strftime('%Y-%m-%d %H:%M')} ---\n")
            for rule in final_list:
                f.write(format_rule(rule) + "\n")
            f.write("]\n")

        print(f"   ✅ SUCCESS: Wrote to -> {new_filename}")

if __name__ == "__main__":
    args = parse_arguments()
    merge_nsg_rules(args.excel_file, args.base_rules, args.repo_root)
