# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for secrets or exploitable flaws.

Email the repository owner (see the GitHub profile for `ritvikindupuri`) with:

- a description of the issue
- affected file paths (never paste secret values)
- reproduction steps that do not include credentials

## Secret handling

- Never commit `.env`, `*.env` (except `.env.example`), or deploy/payload zip archives.
- `ANTHROPIC_API_KEY`, Grafana admin credentials, and cloud credentials must come from the process environment, AWS SSM Parameter Store, or AWS Secrets Manager.
- `deploy_remote.py` builds a deploy archive at run time and refuses to include secret env files.
- `EC2_INSTANCE_ID` must be set in the environment; deploy/SSM helper scripts fail closed if it is unset.

## Known exposure — rotate immediately

A previous commit of `deploy_payload.zip` included a `.env` file with a real-looking `ANTHROPIC_API_KEY`.

**The key must be rotated in the Anthropic console.** Removing the zip from the working tree does **not** remove it from git history. A history rewrite (filter-repo / BFG) is required and is intentionally **not** done in the security hardening PR. Until that rewrite, treat the historical object as public.

Gitleaks CI scans the current working tree (`--no-git`). A full-history scan will fail until the leak is purged.

## Default credentials

Grafana has **no** default `admin`/`admin` password. Set `GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` before `docker compose up`. Prometheus is bound to localhost only and is not opened in the AWS ingress security group.

## Network and access

- Terraform ingress for Grafana (`3000`) and the API gateway (`8000`) requires `allowed_cidr`. `0.0.0.0/0` is rejected.
- SSH/22 is not opened. Use AWS Systems Manager Session Manager.
- Kubernetes defender RBAC is a namespaced Role on `sre-target-apps`, not a ClusterRole.
