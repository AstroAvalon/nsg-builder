"""
MODULE: NSG Rule Validator
AUTHOR: Jules
DATE: 2026-02-19

DESCRIPTION:
  Validates that NSG rules defined in an Excel file (and optional Base Rules)
  are correctly present in the Terraform configuration (.tfvars files).

  It performs a content-based match (ignoring Priority, Name, Description)
  checking: Direction, Access, Protocol, Source, Destination, Destination Port.

USAGE:
  python validator.py <excel_file> [--base-rules <base_rules_file>] [--repo-root <path>]
"""

import pandas as pd
import re
import os
import glob
import argparse
import sys
from typing import Dict, List, Any, Optional

try:
    import azure_helper
except ImportError:
    print("❌ Error: azure_helper module not found.")
    sys.exit(1)

# --- CONFIGURATION ---
OUTPUT_SUFFIX = "_updated"

# --- REGEXES (Matches nsg_merger behavior) ---
RE_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]")
RE_DOT_BETWEEN_NUMBERS = re.compile(r"(\d)\s*\.\s*(\d)")
RE_WHITESPACE = re.compile(r"\s+")

def clean_port(val: str) -> str:
    if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
        return "*"
    cleaned = RE_DOT_BETWEEN_NUMBERS.sub(r"\1,\2", str(val))
    return RE_WHITESPACE.sub("", cleaned).replace(",,", ",").strip(",")

def clean_ip(val: str) -> str:
    if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
        return "*"
    return RE_WHITESPACE.sub("", str(val)).strip(",")

def normalize_protocol(val: str) -> str:
    val = str(val).strip().capitalize()
    if val.upper() in ["ANY", "*"]: return "*"
    if val == "Icmp": return "Icmp"
    if val == "Udp": return "Udp"
    if val == "Tcp": return "Tcp"
    return val

def normalize_access(val: str) -> str:
    val = str(val).strip().capitalize()
    return val if val in ["Allow", "Deny"] else "Allow"

def normalize_direction(val: str) -> str:
    val = str(val).strip().upper()
    if "IN" in val: return "Inbound"
    if "OUT" in val: return "Outbound"
    return "Inbound"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Validate NSG rules against Terraform configuration.")
    parser.add_argument("excel_file", nargs="?", help="Path to the Excel request file")
    parser.add_argument("--base-rules", help="Path to Base Rules Excel file", default=None)
    parser.add_argument("--repo-root", default=".", help="Root directory of the repo")
    return parser.parse_args()

def find_existing_file(subnet_key: str, repo_root: str) -> Optional[str]:
    tfvars_dir = os.path.join(repo_root, "tfvars")
    safe_name = RE_ALPHANUMERIC.sub("", str(subnet_key)).lower()

    # List all auto.tfvars
    all_files = glob.glob(os.path.join(tfvars_dir, "*.auto.tfvars"))
    # Filter out _updated files to find the source of truth (or updated ones if they exist?
    # Usually validation happens against the current state.
    # nsg_merger produces _updated.
    # If _updated exists, we should probably validate against that if the intention is to verify the *proposal*.
    # But usually validator checks the *committed* code.
    # Let's check all valid files (excluding _updated usually, unless we want to check the result of a merge).
    # The requirement says "match each value in the excel exactly with its corresponding tfvar file/rule".
    # I will assume we check the files that are currently valid in the repo.
    
    valid_files = [f for f in all_files if OUTPUT_SUFFIX not in f]
    
    for file_path in valid_files:
        filename = os.path.basename(file_path).lower()
        clean_filename = filename.replace(".auto.tfvars", "").replace("_", "").replace(".", "")
        if safe_name in clean_filename:
            return file_path
    return None

def rules_match(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    # 1. Direction
    if expected['direction'] != actual.get('direction'): return False
    # 2. Access
    if expected['access'] != actual.get('access'): return False
    # 3. Protocol
    # Handle "*" vs "Any" vs "*"
    e_proto = expected['protocol']
    a_proto = actual.get('protocol', '*')
    if e_proto != a_proto:
        # Special case: * matches Any
        if not (e_proto == "*" and a_proto == "*"): # already checked eq
             return False

    # 4. Source Address (Prefix vs Prefixes)
    # Excel usually gives a comma-separated list.
    # Terraform has source_address_prefix (string) OR source_address_prefixes (list).
    # We need to normalize both to a set of strings for comparison.
    e_src = set(expected['source'].split(','))

    a_src_raw = actual.get('source_address_prefix') or actual.get('source_address_prefixes')
    if isinstance(a_src_raw, list):
        a_src = set(a_src_raw)
    else:
        # If it's a string, it might be "*" or a single CIDR or a comma-list (if erroneously put in string field)
        # Usually TF uses list for multiple.
        # But if the validator normalized inputs to comma-string, we split it.
        if a_src_raw is None: a_src = {"*"} # Default?
        else: a_src = set(str(a_src_raw).replace(" ", "").split(','))

    # Special handling for "*"
    if "*" in e_src and "*" in a_src: pass # Match
    elif e_src != a_src: return False

    # 5. Destination Address
    e_dst = set(expected['destination'].split(','))
    a_dst_raw = actual.get('destination_address_prefix') or actual.get('destination_address_prefixes')
    if isinstance(a_dst_raw, list):
        a_dst = set(a_dst_raw)
    else:
        if a_dst_raw is None: a_dst = {"*"}
        else: a_dst = set(str(a_dst_raw).replace(" ", "").split(','))
        
    if "*" in e_dst and "*" in a_dst: pass
    elif e_dst != a_dst: return False

    # 6. Destination Port
    e_port = set(expected['dest_port'].split(','))
    a_port_raw = actual.get('destination_port_range') or actual.get('destination_port_ranges')

    # Terraform ports can be ints or strings.
    if isinstance(a_port_raw, list):
        a_port = set(str(p) for p in a_port_raw)
    else:
        if a_port_raw is None: a_port = {"*"}
        else: a_port = set(str(a_port_raw).replace(" ", "").split(','))

    if "*" in e_port and "*" in a_port: pass
    elif e_port != a_port: return False

    return True

def validate(excel_file, base_rules_file, repo_root):
    # 1. Load Context
    print("ℹ️  Loading Project Context...")
    locals_tf_path = os.path.join(repo_root, "locals.tf")
    project_vars_path = os.path.join(repo_root, "tfvars", "project.auto.tfvars")

    subnet_config = azure_helper.parse_subnet_config(locals_tf_path)
    project_vars = azure_helper.parse_project_tfvars(project_vars_path)

    vnet_cidr = "10.0.0.0/16"
    if project_vars.get('address_space'):
        vnet_cidr = project_vars['address_space'][0]

    # 2. Load Excel Data
    client_rules = []
    if excel_file:
        try:
            df = pd.read_excel(excel_file, dtype=str)
            df.columns = df.columns.str.strip()
            # Remove GatewaySubnet
            df = df[df["Azure Subnet Name"] != "GatewaySubnet"]
            client_rules = df.to_dict('records')
        except Exception as e:
            print(f"❌ Error reading Client Excel: {e}")
            return

    base_rules = []
    if base_rules_file:
        try:
            df_base = pd.read_excel(base_rules_file, dtype=str)
            df_base.columns = df_base.columns.str.strip()
            base_rules = df_base.to_dict('records')
        except Exception as e:
            print(f"❌ Error reading Base Rules Excel: {e}")
            return

    # 3. Resolve Subnet Map (Name -> Key)
    name_to_key = {}
    for k, v in subnet_config.items():
        if "name" in v: name_to_key[v["name"]] = k
        name_to_key[k] = k

    # 4. Build List of Validations
    # List of (SubnetKey, ExpectedRuleDict)
    validations = []

    # A. Client Rules
    for row in client_rules:
        subnet_name = row.get("Azure Subnet Name")
        if pd.isna(subnet_name): continue
        key = name_to_key.get(subnet_name, subnet_name)

        rule = {
            "subnet_key": key,
            "direction": normalize_direction(row["Direction"]),
            "access": normalize_access(row["Access"]),
            "protocol": normalize_protocol(row["Protocol"]),
            "source": clean_ip(row["Source"]),
            "destination": clean_ip(row["Destination"]),
            "dest_port": clean_port(row["Destination Port"]),
            "desc": str(row.get("Description", ""))[:50],
            "origin": "Client Excel"
        }
        validations.append(rule)

    # B. Base Rules
    if base_rules:
        # Base rules apply to ALL subnets with has_nsg = true
        target_keys = {k for k, v in subnet_config.items() if v.get("has_nsg", False)}

        for key in target_keys:
            if str(key).lower() == "gatewaysubnet": continue
            
            # Calculate CIDR
            current_cidr = ""
            conf = subnet_config.get(key)
            if conf:
                current_cidr = azure_helper.calculate_subnet_cidr(
                    vnet_cidr, conf.get("newbits", 0), conf.get("netnum", 0)
                )
            
            for row in base_rules:
                # Replace placeholders
                src = clean_ip(row["Source"]).replace("{{CurrentSubnet}}", current_cidr).replace("{{VNetCIDR}}", vnet_cidr)
                dst = clean_ip(row["Destination"]).replace("{{CurrentSubnet}}", current_cidr).replace("{{VNetCIDR}}", vnet_cidr)

                rule = {
                    "subnet_key": key,
                    "direction": normalize_direction(row["Direction"]),
                    "access": normalize_access(row["Access"]),
                    "protocol": normalize_protocol(row["Protocol"]),
                    "source": src,
                    "destination": dst,
                    "dest_port": clean_port(row["Destination Port"]),
                    "desc": f"[Base] {str(row.get('Description', ''))[:30]}",
                    "origin": "Base Rules"
                }
                validations.append(rule)

    # 5. Execute Validation
    print(f"ℹ️  Validating {len(validations)} rules...")
    
    # Cache parsed TF files to avoid re-reading
    file_cache = {}

    stats = {"ok": 0, "missing": 0, "total": 0}

    for expected in validations:
        stats["total"] += 1
        key = expected['subnet_key']

        # Find File
        if key not in file_cache:
            filepath = find_existing_file(key, repo_root)
            if filepath:
                with open(filepath, "r") as f:
                    file_cache[key] = azure_helper.parse_hcl_rules(f.read())
            else:
                file_cache[key] = None # File missing
        
        actual_rules = file_cache[key]

        if not actual_rules:
            print(f"❌ [{expected['subnet_key']}] Subnet File Missing! Cannot find rule: {expected['desc']}")
            stats["missing"] += 1
            continue

        # Search for match
        found = False
        for actual in actual_rules:
            if rules_match(expected, actual):
                found = True
                break

        if found:
            print(f"✅ [{expected['subnet_key']}] Found: {expected['desc']}")
            stats["ok"] += 1
        else:
            print(f"❌ [{expected['subnet_key']}] MISSING: {expected['desc']}")
            print(f"    Expected: {expected['access']} {expected['direction']} {expected['protocol']} Src:{expected['source']} Dst:{expected['destination']} Port:{expected['dest_port']}")
            stats["missing"] += 1

    # 6. Summary
    print("\n--- Validation Summary ---")
    print(f"Total Rules Checked: {stats['total']}")
    print(f"✅ Present:          {stats['ok']}")
    print(f"❌ Missing:          {stats['missing']}")

    if stats['missing'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    args = parse_arguments()
    if not args.excel_file and not args.base_rules:
        print("❌ Error: Must provide either excel_file or --base-rules")
        sys.exit(1)

    validate(args.excel_file, args.base_rules, args.repo_root)
