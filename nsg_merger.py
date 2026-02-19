"""
MODULE: Azure NSG Rule Merger
VERSION: 2.0 (Sorted & Prioritized)
AUTHOR: DevOps Team (Refactored by Jules)
DATE: 2026-02-19

DESCRIPTION:
  Parses an Excel sheet of firewall requests and merges them into Terraform variables (.tfvars).
  It acts as a "Safe Merger" — it reads the existing state from disk to calculate the next
  available priority ID, ensuring no collisions with manually added rules.

  KEY FEATURES:
  - Separate priority counters for Inbound and Outbound rules.
  - Sorts rules: Inbound first, then Outbound; ordered by Priority.
  - Reconstructs the entire file to ensure clean HCL formatting.

ARCHITECTURAL CONSTRAINTS:
  1. Source of Truth: The existing .auto.tfvars files in the repo.
  2. Naming Convention: "{Subnet}_{In/Out}_{Allow/Deny}{Priority}".
  3. Priority Logic: Independent counters for Inbound/Outbound.
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
# Regex to find a rule block inside the list: { ... }
RE_RULE_BLOCK = re.compile(r"\{\s*(.*?)\s*\}", re.DOTALL)
# Regex to extract key-values inside a block
RE_KV_STRING = re.compile(r'(\w+)\s*=\s*"(.*?)"')
RE_KV_INT = re.compile(r'(\w+)\s*=\s*(\d+)')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Merge NSG rules from Excel to Terraform files.")
    parser.add_argument("excel_file", help="Path to the Excel request file")
    parser.add_argument("--repo-root", default=".", help="Root directory of the repo")
    return parser.parse_args()

def find_existing_file(subnet_name: str, valid_files: List[str]) -> Optional[str]:
    safe_name = RE_ALPHANUMERIC.sub("", str(subnet_name)).lower()
    for file_path in valid_files:
        filename = os.path.basename(file_path).lower()
        if safe_name in filename.replace("_", "").replace(".", ""):
            return file_path
    return None

def parse_hcl_rules(content: str) -> List[Dict[str, Any]]:
    """
    Parses the HCL content to extract a list of rule dictionaries.
    Assumes content is 'Variable = [ { rule }, { rule } ]'
    """
    rules = []
    # Find the list content inside brackets
    list_match = re.search(r"=\s*\[(.*)\]", content, re.DOTALL)
    if not list_match:
        return rules

    inner_content = list_match.group(1)

    for match in RE_RULE_BLOCK.finditer(inner_content):
        block_body = match.group(1)
        rule = {}

        # Extract string fields
        for kv in RE_KV_STRING.finditer(block_body):
            rule[kv.group(1)] = kv.group(2)

        # Extract int fields (priority)
        for kv in RE_KV_INT.finditer(block_body):
            # Prioritize integer capture for 'priority'
            if kv.group(1) == "priority":
                rule[kv.group(1)] = int(kv.group(2))
            else:
                # Other integers? usually strings in HCL but just in case
                rule[kv.group(1)] = int(kv.group(2))

        if rule:
            rules.append(rule)

    return rules

def format_rule(rule: Dict[str, Any]) -> str:
    """
    Formats a single rule dictionary into an HCL block.
    """
    # ensure strictly ordered keys for aesthetics
    order = [
        "name", "description", "priority", "direction", "access", "protocol",
        "source_address_prefix", "source_address_prefixes",
        "source_port_range", "source_port_ranges",
        "destination_address_prefix", "destination_address_prefixes",
        "destination_port_range", "destination_port_ranges"
    ]

    hcl = "  {\n"

    # Process known keys in order
    for key in order:
        if key in rule:
            val = rule[key]
            if isinstance(val, int):
                hcl += f'    {key:<26} = {val}\n'
            else:
                hcl += f'    {key:<26} = "{val}"\n'

    # Process any other keys not in strict order
    for key, val in rule.items():
        if key not in order:
             if isinstance(val, int):
                hcl += f'    {key:<26} = {val}\n'
             else:
                hcl += f'    {key:<26} = "{val}"\n'

    hcl += "  },"
    return hcl

def merge_nsg_rules(excel_path: str, repo_root: str):
    tfvars_dir = os.path.join(repo_root, "tfvars")
    if not os.path.exists(tfvars_dir):
        print(f"❌ Error: Could not find 'tfvars' folder at: {tfvars_dir}")
        return

    # Load Context
    print("ℹ️ Loading Project Configuration...")
    project_vars_path = os.path.join(repo_root, "tfvars", "project.auto.tfvars")
    locals_tf_path = os.path.join(repo_root, "locals.tf")

    project_vars = azure_helper.parse_project_tfvars(project_vars_path) if azure_helper else {}
    subnet_config = azure_helper.parse_subnet_config(locals_tf_path) if azure_helper else {}

    # Load Excel
    try:
        df = pd.read_excel(excel_path, dtype=str)
        df.columns = df.columns.str.strip()
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # Maps
    api_map = {
        "TCP": "Tcp", "UDP": "Udp", "ICMP": "Icmp", "ANY": "*", "*": "*",
        "INBOUND": "Inbound", "OUTBOUND": "Outbound",
        "ALLOW": "Allow", "DENY": "Deny"
    }

    def clean_port(val: str) -> str:
        if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
            return "*"
        cleaned = RE_DOT_BETWEEN_NUMBERS.sub(r"\1,\2", str(val))
        return RE_WHITESPACE.sub("", cleaned).replace(",,", ",").strip(",")

    def clean_ip(val: str) -> str:
        if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
            return "*"
        return RE_WHITESPACE.sub("", str(val)).strip(",")

    all_files = glob.glob(os.path.join(tfvars_dir, "*.auto.tfvars"))
    valid_files = [f for f in all_files if OUTPUT_SUFFIX not in f]

    grouped = df.groupby("Azure Subnet Name")

    for subnet_raw, rules in grouped:
        if pd.isna(subnet_raw): continue
        if str(subnet_raw).lower() == "gatewaysubnet":
            print(f"\n⚠️ Skipping Restricted Subnet: {subnet_raw}")
            continue

        print(f"\nProcessing Subnet: {subnet_raw}")

        existing_file = find_existing_file(subnet_raw, valid_files)

        # State Tracking
        existing_rules = []
        var_name = f"{RE_ALPHANUMERIC.sub('', str(subnet_raw))}_nsg_rules"
        new_filename = ""

        if existing_file:
            print(f"   ↪ Reading Source: {os.path.basename(existing_file)}")
            with open(existing_file, "r") as f:
                content = f.read()
                existing_rules = parse_hcl_rules(content)
                # Try to preserve var name
                m_var = re.search(r"(\w+)\s*=", content)
                if m_var:
                    var_name = m_var.group(1)

            base_name = os.path.basename(existing_file)
            name_part, _ = os.path.splitext(base_name)
            name_part = name_part.replace(".auto", "")
            new_filename = os.path.join(tfvars_dir, f"{name_part}{OUTPUT_SUFFIX}.auto.tfvars")
        else:
            clean_name = RE_ALPHANUMERIC.sub("", str(subnet_raw)).lower()
            new_filename = os.path.join(tfvars_dir, f"nsg_{clean_name}.auto.tfvars")
            print(f"   ↪ Creating NEW file: {os.path.basename(new_filename)}")

        # Initialize Priority Counters
        prio_counters = {"IN": START_PRIORITY, "OUT": START_PRIORITY}
        used_priorities_in = set()
        used_priorities_out = set()

        # Populate used priorities from existing rules
        for r in existing_rules:
            p = r.get("priority")
            d = str(r.get("direction", "")).upper()
            if p:
                if "IN" in d:
                    used_priorities_in.add(p)
                    # Bump counters if necessary to avoid collision
                    if 1000 <= p < 2000 and p >= prio_counters["IN"]:
                        prio_counters["IN"] = p + PRIORITY_STEP
                else:
                    used_priorities_out.add(p)
                    if 1000 <= p < 2000 and p >= prio_counters["OUT"]:
                        prio_counters["OUT"] = p + PRIORITY_STEP

        # --- Azure Drift Detection ---
        drift_rules = []
        if azure_helper and project_vars:
             try:
                # (Existing logic for resolving names...)
                # Simplified for brevity but keeping core logic
                rg_name = azure_helper.get_resource_group_name(project_vars)
                tf_subnet_key = subnet_raw
                has_nsg = True
                # Fuzzy match logic for subnet config...
                def normalize(s): return RE_ALPHANUMERIC.sub("", str(s)).lower()
                norm_raw = normalize(subnet_raw)
                for k, v in subnet_config.items():
                    if normalize(k) == norm_raw or normalize(v.get("name", "")) == norm_raw:
                        tf_subnet_key = k; break

                if subnet_config.get(tf_subnet_key, {}).get("has_nsg", True):
                    nsg_name = azure_helper.get_nsg_name(tf_subnet_key, project_vars.get("environment_level"))
                    sub_id = project_vars.get("customer_subscription_id")

                    print(f"   🔍 Querying Azure NSG: {nsg_name}")
                    azure_rules = azure_helper.fetch_azure_nsg_rules(rg_name, nsg_name, sub_id)

                    for az_rule in azure_rules:
                        # Check used sets based on direction
                        is_inbound = "IN" in az_rule.direction.upper()
                        if (is_inbound and az_rule.priority in used_priorities_in) or \
                           (not is_inbound and az_rule.priority in used_priorities_out):
                            pass
                        else:
                            print(f"   ⚠️  DRIFT: Found Priority {az_rule.priority} in Azure. Importing...")
                            # Create rule dict
                            drift_rules.append({
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
                            })
                            # Mark used
                            if is_inbound: used_priorities_in.add(az_rule.priority)
                            else: used_priorities_out.add(az_rule.priority)

             except Exception as e:
                 print(f"   ❌ Azure Check Warning: {e}")

        # --- Process New Rules (Excel) ---
        new_rules = []

        # First pass: Convert rows to rule dicts and assign priorities
        for _, row in rules.iterrows():
            raw_dir = str(row["Direction"]).upper().strip()
            dir_short = "IN" if "IN" in raw_dir else "OUT"
            is_inbound = (dir_short == "IN")

            # User provided priority?
            prio_val = None
            try:
                if not pd.isna(row["Priority"]) and str(row["Priority"]).strip() != "":
                    prio_val = int(float(row["Priority"]))
            except: pass

            target_set = used_priorities_in if is_inbound else used_priorities_out

            if prio_val:
                if prio_val in target_set:
                    print(f"   ❌ CRITICAL CONFLICT: Priority {prio_val} ({dir_short}) already used. SKIPPING.")
                    continue
            else:
                # Auto-assign
                while prio_counters[dir_short] in target_set:
                    prio_counters[dir_short] += PRIORITY_STEP
                prio_val = prio_counters[dir_short]
                prio_counters[dir_short] += PRIORITY_STEP

            # Add to set
            if is_inbound: used_priorities_in.add(prio_val)
            else: used_priorities_out.add(prio_val)

            # Build Rule
            clean_subnet_name = RE_ALPHANUMERIC.sub("", str(subnet_raw))
            dir_api = api_map.get(raw_dir, "Inbound")
            access_api = api_map.get(str(row["Access"]).upper().strip(), "Allow")
            proto_api = api_map.get(str(row["Protocol"]).upper().strip(), "Tcp")

            new_rules.append({
                "name": f"{clean_subnet_name}_{dir_short}_{access_api}{prio_val}",
                "description": str(row['Description'])[:100],
                "priority": prio_val,
                "direction": dir_api,
                "access": access_api,
                "protocol": proto_api,
                "source_address_prefix": clean_ip(row['Source']),
                "source_port_range": "*",
                "destination_address_prefix": clean_ip(row['Destination']),
                "destination_port_range": clean_port(row['Destination Port'])
            })

        # --- Merge & Sort ---
        final_list = existing_rules + drift_rules + new_rules

        # Sort: Inbound (0) < Outbound (1), then by Priority
        final_list.sort(key=lambda r: (
            0 if "in" in str(r.get("direction")).lower() else 1,
            r.get("priority", 99999)
        ))

        # --- Write File ---
        print(f"   ↪ Writing {len(final_list)} rules (Sorted & Cleaned)...")
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)

        with open(new_filename, "w") as f:
            f.write(f"{var_name} = [\n")

            # Add header timestamp for traceability
            f.write(f"  # --- Updated via Automation {datetime.now().strftime('%Y-%m-%d %H:%M')} ---\n")

            for rule in final_list:
                f.write(format_rule(rule) + "\n")
            f.write("]\n")

        print(f"   ✅ SUCCESS: Wrote to -> {new_filename}")

if __name__ == "__main__":
    args = parse_arguments()
    merge_nsg_rules(args.excel_file, args.repo_root)
