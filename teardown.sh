#!/usr/bin/env bash
# AWS Clean Teardown Script for SRE Colosseum
# Destroys Terraform-managed AWS resources to prevent ongoing charges.

set -euo pipefail

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

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
if [ -z "$REGION" ]; then
    REGION="$(terraform output -raw region 2>/dev/null || echo us-east-1)"
fi
export AWS_REGION="$REGION"
export AWS_DEFAULT_REGION="$REGION"

echo ""
echo "[1/3] Checking current Terraform state..."
if [ -z "$(terraform state list 2>/dev/null || true)" ]; then
    echo "[INFO] No active Terraform resources found. Zero charges running."
    exit 0
fi

echo "[2/3] Destroying Terraform resources (EC2, VPC, S3 deploy bucket, log groups, IAM)..."
terraform destroy -auto-approve

echo "[3/3] Verification (expect terminated / empty)..."
aws ec2 describe-instances --region "$REGION" \
  --filters "Name=tag:Name,Values=sre-enterprise-platform-host" \
  --query "Reservations[].Instances[].{id:InstanceId,state:State.Name}" --output table || true
aws s3 ls --region "$REGION" | grep sre-resilienceops-deploy || echo "(no deploy bucket)"
aws logs describe-log-groups --region "$REGION" \
  --log-group-name-prefix "/sre/autonomous-agent" \
  --query "logGroups[].logGroupName" --output text || true
echo "SSM parameters under /resilienceops are not in Terraform state; delete them if you do not want them reused."

echo ""
echo "[SUCCESS] Terraform-managed AWS infrastructure destroyed."
