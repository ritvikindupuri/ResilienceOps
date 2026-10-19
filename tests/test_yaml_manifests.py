from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_all(rel: str):
    with (ROOT / rel).open(encoding="utf-8") as handle:
        return [doc for doc in yaml.safe_load_all(handle) if doc]


def test_network_policy_targets_victim_namespace():
    docs = _load_all("k8s/agents/agent-sandbox.yaml")
    policy = next(d for d in docs if d.get("kind") == "NetworkPolicy")
    selectors = [
        rule.get("to", [{}])[0].get("namespaceSelector", {}).get("matchLabels", {})
        for rule in policy["spec"]["egress"]
        if rule.get("to")
    ]
    assert any(sel.get("arena.sre.io/role") == "victim" for sel in selectors)
    assert all(sel.get("platform.sre.io/role") != "workload" for sel in selectors)
    vpc_rule = next(
        rule
        for rule in policy["spec"]["egress"]
        if (rule.get("to") or [{}])[0].get("ipBlock", {}).get("cidr") == "10.0.0.0/16"
    )
    ports = {item["port"] for item in vpc_rule["ports"]}
    assert ports == {8000, 8001, 8002, 9090}


def test_blue_team_sa_is_in_sandbox_namespace():
    sandbox_docs = _load_all("k8s/agents/agent-sandbox.yaml")
    rbac_docs = _load_all("k8s/base/namespace-rbac.yaml")
    sas = [
        d for d in sandbox_docs + rbac_docs
        if d.get("kind") == "ServiceAccount" and d["metadata"]["name"] == "sre-defender-sa"
    ]
    assert sas
    assert all(sa["metadata"]["namespace"] == "sre-agent-sandbox" for sa in sas)

    binding = next(d for d in rbac_docs if d.get("kind") == "RoleBinding")
    assert binding["metadata"]["namespace"] == "sre-target-apps"
    assert binding["roleRef"]["kind"] == "Role"
    assert binding["subjects"][0]["namespace"] == "sre-agent-sandbox"

    kinds = {d.get("kind") for d in rbac_docs}
    assert "ClusterRole" not in kinds
    assert "ClusterRoleBinding" not in kinds


def test_blue_team_pod_uses_sandbox_sa():
    docs = _load_all("k8s/agents/agent-sandbox.yaml")
    dep = next(d for d in docs if d.get("kind") == "Deployment" and d["metadata"]["name"] == "blue-team-operator")
    assert dep["spec"]["template"]["spec"]["serviceAccountName"] == "sre-defender-sa"


def test_sandbox_pods_use_working_dir_app():
    docs = _load_all("k8s/agents/agent-sandbox.yaml")
    for name in ("red-team-sandbox", "blue-team-operator"):
        dep = next(d for d in docs if d.get("kind") == "Deployment" and d["metadata"]["name"] == name)
        container = dep["spec"]["template"]["spec"]["containers"][0]
        assert container["workingDir"] == "/app", name
        mounts = {m["mountPath"] for m in container.get("volumeMounts", [])}
        assert "/app" in mounts, name
