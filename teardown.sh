#!/usr/bin/env bash
# AWS Clean Teardown Script for SRE Colosseum
# Destroys 100% of AWS cloud resources to prevent ongoing charges.

set -e

echo "=========================================================="
echo "   SRE COLOSSEUM - AWS CLEAN INFRASTRUCTURE TEARDOWN"
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"

if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "[ERROR] Terraform directory not found at $TERRAFORM_DIR"
    exit 1
fi

cd "$TERRAFORM_DIR"

echo ""
echo "[1/2] Checking current Terraform state..."
if [ -z "$(terraform state list 2>/dev/null)" ]; then
    echo "[INFO] No active Terraform resources found. Zero charges running."
    exit 0
fi

echo "[2/2] Destroying all AWS resources (EC2, VPC, Subnets, SG, IAM, IGW)..."
terraform destroy -auto-approve

echo ""
echo "[SUCCESS] All AWS infrastructure cleanly destroyed. ZERO residual cost."
