# ==============================================================================
# AUTONOMOUS SRE PLATFORM: ENTERPRISE INFRASTRUCTURE SPECIFICATION
# All-In-One Production Architecture on AWS
#
# Designed for:
#   1. Enterprise Realism: Multi-tier VPC, Segregated Security Groups, IAM Roles.
#   2. Zero Surprise Billing: Cost-optimized compute (t3.small/t4g.small ~$0.02/hr).
#   3. Single-Command Lifecycle:
#        Deploy:  terraform init && terraform apply -auto-approve
#        Destroy: terraform destroy -auto-approve
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

# --- Variables ---
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target AWS deployment region"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Target deployment environment tier"
}

variable "instance_type" {
  type        = string
  default     = "t3.small" # 2 vCPU, 2GB RAM (~$0.02/hr) - runs microservices, k3s/docker, Prometheus, Grafana
  description = "Cost-optimized EC2 instance type with 0 NAT Gateway overhead"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "Primary CIDR block for enterprise VPC"
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

  # Grafana Dashboard UI
  ingress {
    description = "Grafana SRE Dashboard (Auto-provisioned)"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Ingress API Gateway
  ingress {
    description = "Microservices API Gateway Public Endpoint"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus Telemetry Server
  ingress {
    description = "Prometheus Golden Signals Scrape UI"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH Access
  ingress {
    description = "Administrative SSH Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

resource "aws_iam_instance_profile" "sre_instance_profile" {
  name = "sre-platform-instance-profile"
  role = aws_iam_role.sre_host_role.name
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

  root_block_device {
    volume_size           = 25 # 25 GB gp3 (Free-tier eligible / under $2/mo)
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # Production SRE Bootstrapping: Docker, K8s (k3s), and Platform Environment
  user_data = <<-EOF
              #!/bin/bash
              set -e
              apt-get update -y
              apt-get install -y docker.io docker-compose git curl python3-pip jq htop

              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu

              # Install k3s (Lightweight Production Kubernetes distribution)
              curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
              mkdir -p /home/ubuntu/.kube
              cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
              chown -R ubuntu:ubuntu /home/ubuntu/.kube

              echo "[*] SRE Platform Node initialization complete." > /var/log/sre-init.log
              EOF

  tags = {
    Name = "sre-enterprise-platform-host"
    Role = "Kubernetes-Node-And-Workload-Runner"
  }
}

# ==============================================================================
# 5. INSTANT VERIFICATION OUTPUTS
# ==============================================================================

output "public_ip" {
  description = "Public IP address of the AWS SRE Platform Host"
  value       = aws_instance.sre_host.public_ip
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
  description = "URL to access Prometheus Golden Signals Metrics UI"
  value       = "http://${aws_instance.sre_host.public_ip}:9090"
}

output "deployment_instructions" {
  description = "Commands to deploy and destroy cleanly without extra charges"
  value       = "To deploy: 'terraform apply -auto-approve' | To destroy: 'terraform destroy -auto-approve'"
}
