# ==============================================================================
# AUTONOMOUS SRE PLATFORM: ENTERPRISE INFRASTRUCTURE SPECIFICATION
# All-In-One Production Architecture on AWS
#
# Designed for:
#   1. Enterprise Realism: Multi-tier VPC, Segregated Security Groups, IAM Roles.
#   2. Zero Surprise Billing: default t3.medium (~$0.0416/hr + ~$0.005/hr public IPv4)
#      for Compose + k3s + agents. Optional t3.small (~$0.0208/hr + IPv4) is tight.
#   3. Single-Command Lifecycle:
#        Deploy:  terraform init && terraform apply
#        Destroy: terraform destroy
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Platform    = "Autonomous-SRE-Platform"
      Environment = var.environment
      ManagedBy   = "Terraform"
      CostCenter  = "SRE-Resilience-Lab"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# --- Variables ---
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target AWS deployment region. Export AWS_REGION to the same value in your shell."
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Target deployment environment tier"
}

variable "instance_type" {
  type        = string
  # 2 vCPU / 4 GiB. Compose (Postgres, Redis, Prometheus 1s scrape, Grafana, 5 Python
  # services, Alertmanager, incident-bridge) + k3s + optional agent-sandbox needs
  # more than t3.small's 2 GiB. On-demand us-east-1 Linux ~$0.0416/hr plus public
  # IPv4 ~$0.005/hr (~$1.12/day). Override to t3.small for a Compose-only tight lab.
  default     = "t3.medium"
  description = "EC2 instance type. Default t3.medium for Compose+k3s+agents; t3.small is optional and tight."
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "Primary CIDR block for enterprise VPC"
}

variable "allowed_cidr" {
  type        = string
  description = "CIDR allowed to reach Grafana (3000) and the API Gateway (8000). Must not be 0.0.0.0/0. SSH/22 is not opened; use AWS SSM for host access. SSM does not replace this CIDR for browser access to Grafana/API unless you SSM port-forward."

  validation {
    condition     = var.allowed_cidr != "0.0.0.0/0" && can(cidrhost(var.allowed_cidr, 0))
    error_message = "allowed_cidr must be a specific CIDR block; 0.0.0.0/0 is not permitted."
  }
}

variable "ssm_param_prefix" {
  type        = string
  default     = "/resilienceops"
  description = "SSM Parameter Store prefix the instance may read (SecureString secrets written by scripts/put_lab_secrets.py)."
}

# ==============================================================================
# 1. ENTERPRISE NETWORK TOPOLOGY (VPC & MULTI-TIER SEGMENTATION)
# ==============================================================================

resource "aws_vpc" "sre_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "sre-enterprise-vpc"
    Tier = "Network-Core"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.sre_vpc.id

  tags = {
    Name = "sre-enterprise-igw"
  }
}

# Tier 1: Public Ingress Subnet (ALB / Ingress Gateway / Grafana)
resource "aws_subnet" "public_ingress" {
  vpc_id                  = aws_vpc.sre_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "sre-subnet-public-ingress"
    Tier = "Public-Ingress"
  }
}

# Tier 2: Application Workload Subnet (Microservices Cluster)
resource "aws_subnet" "app_workloads" {
  vpc_id            = aws_vpc.sre_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "sre-subnet-app-workloads"
    Tier = "Application-Workloads"
  }
}

# Tier 3: Data & Cache Subnet (Redis & Persistence)
resource "aws_subnet" "data_persistence" {
  vpc_id            = aws_vpc.sre_vpc.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "sre-subnet-data-persistence"
    Tier = "Data-Persistence"
  }
}

# Ingress Routing Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.sre_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "sre-public-route-table"
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_ingress.id
  route_table_id = aws_route_table.public_rt.id
}

# ==============================================================================
# 2. DEFENSE-IN-DEPTH SECURITY GROUPS (LEAST-PRIVILEGE SEGREGATION)
# ==============================================================================

# Public Ingress & Observability SG
resource "aws_security_group" "ingress_sg" {
  name        = "sre-ingress-sg"
  description = "Allows public traffic to API Gateway and Grafana Observability Dashboard"
  vpc_id      = aws_vpc.sre_vpc.id

  # Grafana Dashboard UI — restricted to the operator CIDR
  ingress {
    description = "Grafana SRE Dashboard (restricted CIDR)"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  # Ingress API Gateway — restricted to the operator CIDR
  ingress {
    description = "Microservices API Gateway (restricted CIDR)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  # Prometheus 9090 is intentionally absent: the internet must not reach it.
  # Grafana :3000 and API :8000 are the only ingress_sg openings (allowed_cidr).
  # On the host, Compose binds 127.0.0.1:9090 (SSM port forwarding) and
  # deploy_remote.py also binds the instance private IP so same-host k3s pods
  # can query :9090 via local delivery (no security-group hop, never 0.0.0.0).
  # SSH/22 is not opened. Use AWS Systems Manager Session Manager for access.

  # Outbound egress (package downloads, container image registries)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sre-ingress-sg"
  }
}

# Application & Internal Workload SG (Restricted to internal cluster communication)
resource "aws_security_group" "internal_app_sg" {
  name        = "sre-internal-app-sg"
  description = "Enforces least privilege: restricts inter-service communication"
  vpc_id      = aws_vpc.sre_vpc.id

  ingress {
    description     = "Allows API Gateway to reach internal microservices"
    from_port       = 8001
    to_port         = 8002
    protocol        = "tcp"
    security_groups = [aws_security_group.ingress_sg.id]
  }

  ingress {
    description = "Allows Prometheus scrape across all internal pods"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sre-internal-app-sg"
  }
}

# ==============================================================================
# 3. PRODUCTION IAM INSTANCE PROFILE (ENTERPRISE LEAST-PRIVILEGE)
# ==============================================================================

resource "aws_iam_role" "sre_host_role" {
  name = "sre-platform-host-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "sre-host-iam-role"
  }
}

# Attach AWS Systems Manager (SSM) Policy - Allows secure browser shell without opening port 22
resource "aws_iam_role_policy_attachment" "ssm_attach" {
  role       = aws_iam_role.sre_host_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "host_inline" {
  name = "sre-platform-host-inline"
  role = aws_iam_role.sre_host_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SsmParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_param_prefix}/*"
      },
      {
        Sid    = "DecryptSsmSecureString"
        Effect = "Allow"
        Action = ["kms:Decrypt"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "ssm.${var.aws_region}.amazonaws.com"
          }
        }
      },
      {
        Sid      = "DeployBucketRead"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.deploy.arn}/*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups"
        ]
        Resource = [
          aws_cloudwatch_log_group.audit.arn,
          "${aws_cloudwatch_log_group.audit.arn}:*",
          aws_cloudwatch_log_group.incidents.arn,
          "${aws_cloudwatch_log_group.incidents.arn}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "sre_instance_profile" {
  name = "sre-platform-instance-profile"
  role = aws_iam_role.sre_host_role.name
}

# ==============================================================================
# 3b. DEPLOY BUCKET + CLOUDWATCH LOG GROUPS
# Zip payloads go here so SSM SendCommand stays under the 100 KB document limit.
# Presigned GET is generated by deploy_remote.py; objects expire after 1 day.
# Log groups match agents/config.py defaults (README CloudWatch best-effort path).
# Dashboards are still created by helper scripts, not Terraform.
# ==============================================================================

resource "aws_s3_bucket" "deploy" {
  bucket        = "sre-resilienceops-deploy-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  force_destroy = true

  tags = {
    Name = "sre-resilienceops-deploy"
  }
}

resource "aws_s3_bucket_ownership_controls" "deploy" {
  bucket = aws_s3_bucket.deploy.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "deploy" {
  bucket                  = aws_s3_bucket.deploy.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "deploy" {
  bucket = aws_s3_bucket.deploy.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "deploy" {
  bucket = aws_s3_bucket.deploy.id
  rule {
    id     = "expire-payloads"
    status = "Enabled"
    filter {
      prefix = ""
    }
    expiration {
      days = 1
    }
  }
}

resource "aws_cloudwatch_log_group" "audit" {
  name              = "/sre/autonomous-agent-audit"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "incidents" {
  name              = "/sre/autonomous-agent-incidents"
  retention_in_days = 7
}

# ==============================================================================
# 4. SRE PLATFORM HOST WITH AUTOMATED WORKLOAD BOOTSTRAPPING
# ==============================================================================

data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "sre_host" {
  ami                  = data.aws_ami.ubuntu.id
  instance_type        = var.instance_type
  subnet_id            = aws_subnet.public_ingress.id
  iam_instance_profile = aws_iam_instance_profile.sre_instance_profile.name

  vpc_security_group_ids = [
    aws_security_group.ingress_sg.id,
    aws_security_group.internal_app_sg.id
  ]

  associate_public_ip_address = true

  # Containers/agents need hop_limit >= 2 to reach IMDSv2 from docker/k3s.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  root_block_device {
    volume_size           = 25 # 25 GB gp3 (Free-tier eligible / under $2/mo)
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # Production SRE Bootstrapping: Docker Compose v2, k3s, awscli, swap
  user_data = <<-EOF
              #!/bin/bash
              set -e
              apt-get update -y
              apt-get install -y docker.io docker-compose-v2 awscli unzip git curl python3-pip jq htop

              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu

              # 2G swap as a safety net if Compose + k3s spike memory
              if [ ! -f /swapfile ]; then
                fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
                chmod 600 /swapfile
                mkswap /swapfile
                swapon /swapfile
                echo '/swapfile none swap sw 0 0' >> /etc/fstab
              fi

              # Install k3s (Lightweight Production Kubernetes distribution)
              curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
              mkdir -p /home/ubuntu/.kube
              cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
              chown -R ubuntu:ubuntu /home/ubuntu/.kube

              docker compose version > /var/log/sre-init.log 2>&1 || true
              echo "[*] SRE Platform Node initialization complete." >> /var/log/sre-init.log
              EOF

  tags = {
    Name = "sre-enterprise-platform-host"
    Role = "Kubernetes-Node-And-Workload-Runner"
  }

  depends_on = [
    aws_iam_role_policy_attachment.ssm_attach,
    aws_iam_role_policy.host_inline,
    aws_iam_instance_profile.sre_instance_profile
  ]
}

# ==============================================================================
# 5. INSTANT VERIFICATION OUTPUTS
# ==============================================================================

output "public_ip" {
  description = "Public IP address of the AWS SRE Platform Host"
  value       = aws_instance.sre_host.public_ip
}

output "private_ip" {
  description = "Private IP of the host. Use as orchestrator --target-ip from the k3s sandbox (Compose apps are not in-cluster)."
  value       = aws_instance.sre_host.private_ip
}

output "instance_id" {
  description = "EC2 instance id for EC2_INSTANCE_ID / deploy_remote.py / SSM"
  value       = aws_instance.sre_host.id
}

output "region" {
  description = "AWS region. Export as AWS_REGION / AWS_DEFAULT_REGION before CLI calls."
  value       = var.aws_region
}

output "deploy_bucket" {
  description = "S3 bucket for deploy_remote.py zip payloads (avoids the 100 KB SSM SendCommand limit)"
  value       = aws_s3_bucket.deploy.bucket
}

output "grafana_url" {
  description = "URL to access the live Grafana SRE Dashboard"
  value       = "http://${aws_instance.sre_host.public_ip}:3000"
}

output "api_gateway_url" {
  description = "URL to access the live Microservices Ingress Gateway"
  value       = "http://${aws_instance.sre_host.public_ip}:8000"
}

output "prometheus_url" {
  description = "Prometheus is not in ingress_sg. SSM port-forwards 127.0.0.1:9090; k3s uses the instance private IP (local delivery)."
  value       = "http://127.0.0.1:9090 (SSM); k3s uses http://<private_ip>:9090 (no SG 9090)"
}

output "deployment_instructions" {
  description = "Commands to deploy and destroy cleanly without extra charges"
  value       = "export AWS_REGION=$(terraform output -raw region); python3 scripts/put_lab_secrets.py --region $AWS_REGION; python3 deploy_remote.py --region $AWS_REGION | To destroy: terraform destroy"
}
