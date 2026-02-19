#!/bin/bash

# Configuration
VARS_DIR="./tfvars"
PLAN_FILE="tfplan"

# 1. Check if the vars directory exists
if [ ! -d "$VARS_DIR" ]; then
    echo "❌ Error: Directory '$VARS_DIR' not found."
    exit 1
fi

# 2. Build the var-file arguments dynamically
# This finds all .tfvars files and prepends -var-file= to each
VAR_ARGS=""
for file in "$VARS_DIR"/*.tfvars; do
    [ -e "$file" ] || continue # Handle empty directory case
    VAR_ARGS="$VAR_ARGS -var-file=$file"
done

# 3. Execution Logic
COMMAND=$1
OPTION=$2

case $COMMAND in
    plan)
        echo "catalyst 🚀 Running Terraform Plan..."
        terraform plan $VAR_ARGS -out=$PLAN_FILE
        ;;
    apply)
        if [ -f "$PLAN_FILE" ]; then
            echo "✅ Applying existing plan: $PLAN_FILE"
            terraform apply "$PLAN_FILE"
        else
            echo "⚠️ No plan file found. Running direct apply..."
            terraform apply $VAR_ARGS -auto-approve
        fi
        ;;
    destroy)
        if [[ "$OPTION" == "-y" || "$OPTION" == "--force" ]]; then
            echo "🔥 Force destroying infrastructure..."
            terraform destroy $VAR_ARGS -auto-approve
        else
            read -p "Are you sure you want to DESTROY? (y/n): " confirm
            if [[ $confirm == "y" ]]; then
                echo "🔥 Destroying infrastructure..."
                terraform destroy $VAR_ARGS -auto-approve
            else
                echo "❌ Destroy cancelled."
            fi
        fi
        ;;
    *)
        echo "Usage: $0 {plan|apply|destroy [-y|--force]}"
        exit 1
        ;;
esac
