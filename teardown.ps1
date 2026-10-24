# Cross-platform AWS Teardown Script for ResilienceOps
# Destroys Terraform-managed AWS resources to prevent ongoing charges.

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   RESILIENCEOPS - AWS CLEAN INFRASTRUCTURE TEARDOWN" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Join-Path $ScriptDir "terraform"

if (-not (Test-Path $TerraformDir)) {
    Write-Host "[ERROR] Terraform directory not found at $TerraformDir" -ForegroundColor Red
    exit 1
}

Push-Location $TerraformDir

try {
    $Region = $env:AWS_REGION
    if (-not $Region) { $Region = $env:AWS_DEFAULT_REGION }
    if (-not $Region) {
        $Region = terraform output -raw region 2>$null
        if (-not $Region) { $Region = "us-east-1" }
    }
    $env:AWS_REGION = $Region
    $env:AWS_DEFAULT_REGION = $Region

    Write-Host "`n[1/4] Checking current Terraform state..." -ForegroundColor Yellow
    $StateList = terraform state list 2>$null
    if (-not $StateList) {
        Write-Host "[INFO] No active Terraform resources found." -ForegroundColor Green
    } else {
        Write-Host "[2/4] Destroying Terraform resources (EC2, VPC, S3 deploy bucket, log groups, IAM)..." -ForegroundColor Yellow
        terraform destroy -auto-approve
    }

    Write-Host "[3/4] Deleting SSM parameters under /resilienceops (not in Terraform state)..." -ForegroundColor Yellow
    $ParamNames = aws ssm get-parameters-by-path --path /resilienceops --recursive `
      --query 'Parameters[].Name' --output text --region $Region 2>$null
    if (-not $ParamNames) {
        Write-Host "(no /resilienceops parameters)"
    } else {
        $chunks = @($ParamNames -split '\s+' | Where-Object { $_ })
        for ($i = 0; $i -lt $chunks.Count; $i += 10) {
            $batch = $chunks[$i..([Math]::Min($i + 9, $chunks.Count - 1))]
            aws ssm delete-parameters --names $batch --region $Region
        }
    }

    Write-Host "[4/4] Verification (expect terminated / empty)..." -ForegroundColor Yellow
    aws ec2 describe-instances --region $Region `
      --filters "Name=tag:Name,Values=sre-enterprise-platform-host" `
      --query "Reservations[].Instances[].{id:InstanceId,state:State.Name}" --output table
    aws s3 ls --region $Region | Select-String "sre-resilienceops-deploy"
    aws logs describe-log-groups --region $Region `
      --log-group-name-prefix "/sre/autonomous-agent" `
      --query "logGroups[].logGroupName" --output text
    Write-Host "If you attached the operator managed policy, detach and delete it from an admin login:"
    Write-Host "  ACCOUNT_ID=`$(aws sts get-caller-identity --query Account --output text --region `$AWS_REGION)"
    Write-Host "  POLICY_ARN=`"arn:aws:iam::`${ACCOUNT_ID}:policy/ResilienceOpsDeployer`""
    Write-Host "  aws iam detach-user-policy --user-name <YOUR_IAM_USER> --policy-arn `$POLICY_ARN"
    Write-Host "  aws iam detach-role-policy --role-name <YOUR_IAM_ROLE> --policy-arn `$POLICY_ARN"
    Write-Host "  aws iam delete-policy --policy-arn `$POLICY_ARN"

    Write-Host "`n[SUCCESS] Terraform-managed AWS infrastructure destroyed." -ForegroundColor Green
}
catch {
    Write-Host "`n[ERROR] Teardown encountered an error: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
finally {
    Pop-Location
}
