# Cross-platform AWS Teardown Script for SRE Colosseum
# Destroys Terraform-managed AWS resources to prevent ongoing charges.

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SRE COLOSSEUM - AWS CLEAN INFRASTRUCTURE TEARDOWN" -ForegroundColor Cyan
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

    Write-Host "`n[1/3] Checking current Terraform state..." -ForegroundColor Yellow
    $StateList = terraform state list 2>$null
    if (-not $StateList) {
        Write-Host "[INFO] No active Terraform resources found. Zero charges running." -ForegroundColor Green
        Pop-Location
        exit 0
    }

    Write-Host "[2/3] Destroying Terraform resources (EC2, VPC, S3 deploy bucket, log groups, IAM)..." -ForegroundColor Yellow
    terraform destroy -auto-approve

    Write-Host "[3/3] Verification (expect terminated / empty)..." -ForegroundColor Yellow
    aws ec2 describe-instances --region $Region `
      --filters "Name=tag:Name,Values=sre-enterprise-platform-host" `
      --query "Reservations[].Instances[].{id:InstanceId,state:State.Name}" --output table
    aws s3 ls --region $Region | Select-String "sre-resilienceops-deploy"
    aws logs describe-log-groups --region $Region `
      --log-group-name-prefix "/sre/autonomous-agent" `
      --query "logGroups[].logGroupName" --output text
    Write-Host "SSM parameters under /resilienceops are not in Terraform state; delete them if you do not want them reused."

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
