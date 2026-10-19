# Architecture logos

Icons in this folder are inlined into `docs/architecture.svg` by
`scripts/build_architecture.py`.

| File | Source |
| --- | --- |
| `aws-ec2.svg`, `aws-iam.svg`, `aws-ssm.svg` | [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) (2D service icons). AWS, the AWS logo, and AWS service names are trademarks of Amazon.com, Inc. or its affiliates. |
| `aws-vpc.svg`, `aws-subnet-public.svg` | AWS Architecture Icons **group** marks (`Virtual-private-cloud-VPC_32`, `Public-subnet_32`). The diagram draws the matching VPC (purple dashed) and public-subnet (green) group boundaries; the security-group marker is the official dashed-red group treatment (no 32px group icon in the current package). |
| `k3s.svg` | Official k3s mark from [CNCF artwork](https://github.com/cncf/artwork) (`projects/k3s`). |
| `alertmanager.svg` | Grafana Alertmanager data-source mark (Prometheus flame + bell) from the Grafana project. |
| `docker.svg`, `fastapi.svg`, `redis.svg`, `postgresql.svg`, `prometheus.svg`, `grafana.svg`, `kubernetes.svg`, `github.svg`, `terraform.svg` | Official brand glyphs via [Simple Icons](https://simpleicons.org/) (CC0 1.0), colored with each project’s documented brand hex. |

Generic person / clock / bell / document / traffic marks, and the red Grok
hexagon avatar (`#FF3E51`, copied from the Identity Mapper shape in
[grok-bot-aws-attack-path-team](https://github.com/ritvikindupuri/grok-bot-aws-attack-path-team)),
are drawn in `scripts/build_architecture.py`.
