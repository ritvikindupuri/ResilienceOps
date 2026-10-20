# Architecture logos

Icons in this folder are inlined into `docs/architecture.svg` by
`scripts/build_architecture.py`.

| File | Source |
| --- | --- |
| `aws-ec2.svg`, `aws-s3.svg`, `aws-ssm.svg`, `aws-iam.svg` | [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) service icons from **Icon-package_07312026** (`Arch_Amazon-EC2_64`, `Arch_Amazon-Simple-Storage-Service_64`, `Arch_AWS-Systems-Manager_64`). AWS, the AWS logo, and AWS service names are trademarks of Amazon.com, Inc. or its affiliates. |
| `aws-param-store.svg` | Same package, **resource** icon `Res_AWS-Systems-Manager_Parameter-Store_48`. |
| `aws-logo.svg` | Same package, group mark `AWS-Cloud-logo_32`. |
| `aws-cloudwatch.svg` | Compact AWS-style mark kept for unused/legacy figure variants. |
| `aws-vpc.svg`, `aws-subnet-public.svg` | AWS Architecture Icons **group** marks (`Virtual-private-cloud-VPC_32`, `Public-subnet_32`). |
| `k3s.svg` | Official k3s mark from [CNCF artwork](https://github.com/cncf/artwork) (`projects/k3s`). |
| `alertmanager.svg` | Grafana Alertmanager data-source mark (Prometheus flame + bell) from the Grafana project. |
| `docker.svg`, `fastapi.svg`, `redis.svg`, `postgresql.svg`, `prometheus.svg`, `grafana.svg`, `kubernetes.svg`, `github.svg`, `terraform.svg` | Official brand glyphs via [Simple Icons](https://simpleicons.org/) (CC0 1.0), colored with each project’s documented brand hex. |

Generic person / clock / bell / document / traffic marks, and the red Grok
hexagon avatar (`#FF3E51`, copied from the Identity Mapper shape in
[grok-bot-aws-attack-path-team](https://github.com/ritvikindupuri/grok-bot-aws-attack-path-team)),
are drawn in `scripts/build_architecture.py`.
