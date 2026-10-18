import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger("sre-arena.k8s")


class K8sToolKit:
    """Cluster operations via the Python kubernetes client (kubectl optional fallback)."""

    def __init__(self, namespace: str = "sre-target-apps"):
        self.namespace = namespace
        self.core = None
        self.apps = None
        self.backend = None
        self.k8s_available = self._init_clients()

    def _init_clients(self) -> bool:
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
            self.core = client.CoreV1Api()
            self.apps = client.AppsV1Api()
            self.backend = "python"
            return True
        except Exception as exc:
            logger.info("Python kubernetes client unavailable (%s); trying kubectl", exc)

        try:
            import subprocess
            res = subprocess.run(
                ["kubectl", "version", "--client", "-o", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                self.backend = "kubectl"
                return True
        except Exception:
            pass
        return False

    def run_kubectl(self, args: List[str]) -> Dict[str, Any]:
        """Runs a kubectl command safely and returns output or error."""
        import subprocess

        cmd = ["kubectl"] + args + ["-n", self.namespace]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "exit_code": res.returncode,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    def get_pods(self) -> List[Dict[str, Any]]:
        """Returns parsed list of pods and statuses."""
        if self.backend == "python" and self.core is not None:
            try:
                data = self.core.list_namespaced_pod(self.namespace)
                pods = []
                for item in data.items:
                    restarts = 0
                    ready = False
                    container_statuses = item.status.container_statuses or []
                    if container_statuses:
                        restarts = sum(cs.restart_count or 0 for cs in container_statuses)
                        ready = all(bool(cs.ready) for cs in container_statuses)
                    pods.append({
                        "name": item.metadata.name,
                        "phase": item.status.phase or "Unknown",
                        "ready": ready,
                        "restarts": restarts,
                        "labels": item.metadata.labels or {},
                    })
                return pods
            except Exception as e:
                logger.error(f"Error listing pods: {e}")
                return []

        if self.backend != "kubectl":
            return []
        import json
        res = self.run_kubectl(["get", "pods", "-o", "json"])
        if not res["success"] or not res["stdout"]:
            return []
        try:
            data = json.loads(res["stdout"])
            pods = []
            for item in data.get("items", []):
                name = item["metadata"]["name"]
                status = item["status"].get("phase", "Unknown")
                restarts = 0
                ready = False
                container_statuses = item["status"].get("containerStatuses", [])
                if container_statuses:
                    restarts = sum(cs.get("restartCount", 0) for cs in container_statuses)
                    ready = all(cs.get("ready", False) for cs in container_statuses)
                pods.append({
                    "name": name,
                    "phase": status,
                    "ready": ready,
                    "restarts": restarts,
                    "labels": item["metadata"].get("labels", {}),
                })
            return pods
        except Exception as e:
            logger.error(f"Error parsing pods: {e}")
            return []

    def get_recent_events(self, limit: int = 15) -> List[Dict[str, str]]:
        """Retrieves recent warning and error events in namespace."""
        if self.backend == "python" and self.core is not None:
            try:
                data = self.core.list_namespaced_event(self.namespace)
                items = list(data.items)[-limit:]
                events = []
                for item in items:
                    involved = item.involved_object
                    events.append({
                        "type": item.type or "Normal",
                        "reason": item.reason or "Unknown",
                        "message": item.message or "",
                        "object": f"{getattr(involved, 'kind', '')}/{getattr(involved, 'name', '')}",
                    })
                return events
            except Exception:
                return []

        if self.backend != "kubectl":
            return []
        import json
        res = self.run_kubectl(["get", "events", "--sort-by=.metadata.creationTimestamp", "-o", "json"])
        if not res["success"] or not res["stdout"]:
            return []
        try:
            data = json.loads(res["stdout"])
            events = []
            for item in data.get("items", [])[-limit:]:
                events.append({
                    "type": item.get("type", "Normal"),
                    "reason": item.get("reason", "Unknown"),
                    "message": item.get("message", ""),
                    "object": f"{item.get('involvedObject', {}).get('kind', '')}/{item.get('involvedObject', {}).get('name', '')}",
                })
            return events
        except Exception:
            return []

    def get_pod_logs(self, pod_name: str, tail: int = 50) -> str:
        """Retrieves standard and previous logs of a pod."""
        if self.backend == "python" and self.core is not None:
            try:
                return self.core.read_namespaced_pod_log(pod_name, self.namespace, tail_lines=tail)
            except Exception:
                try:
                    return "[PREVIOUS CONTAINER CRASH LOGS]:\n" + self.core.read_namespaced_pod_log(
                        pod_name, self.namespace, tail_lines=tail, previous=True
                    )
                except Exception as e:
                    return str(e)

        res = self.run_kubectl(["logs", pod_name, f"--tail={tail}"])
        if res["success"]:
            return res["stdout"]
        res_prev = self.run_kubectl(["logs", pod_name, f"--tail={tail}", "--previous"])
        if res_prev["success"]:
            return f"[PREVIOUS CONTAINER CRASH LOGS]:\n{res_prev['stdout']}"
        return res["stderr"]

    def rollout_undo(self, deployment: str) -> Dict[str, Any]:
        """Rolls back a deployment to previous revision."""
        if self.backend == "python" and self.apps is not None:
            try:
                dep = self.apps.read_namespaced_deployment(deployment, self.namespace)
                labels = (dep.spec.selector.match_labels or {}) if dep.spec.selector else {}
                selector = ",".join(f"{k}={v}" for k, v in labels.items())
                rss = self.apps.list_namespaced_replica_set(self.namespace, label_selector=selector)
                items = sorted(
                    rss.items,
                    key=lambda rs: int((rs.metadata.annotations or {}).get("deployment.kubernetes.io/revision", "0")),
                )
                if len(items) < 2:
                    return {"success": False, "stdout": "", "stderr": "No previous revision", "exit_code": 1}
                prev = items[-2]
                body = {"spec": {"template": prev.spec.template}}
                self.apps.patch_namespaced_deployment(deployment, self.namespace, body)
                return {"success": True, "stdout": f"rolled back {deployment}", "stderr": "", "exit_code": 0}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e), "exit_code": 1}
        return self.run_kubectl(["rollout", "undo", f"deployment/{deployment}"])

    def restart_deployment(self, deployment: str) -> Dict[str, Any]:
        """Performs rolling restart of deployment."""
        if self.backend == "python" and self.apps is not None:
            try:
                now = datetime.now(timezone.utc).isoformat()
                body = {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {"kubectl.kubernetes.io/restartedAt": now}
                            }
                        }
                    }
                }
                self.apps.patch_namespaced_deployment(deployment, self.namespace, body)
                return {"success": True, "stdout": f"restarted {deployment}", "stderr": "", "exit_code": 0}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e), "exit_code": 1}
        return self.run_kubectl(["rollout", "restart", f"deployment/{deployment}"])

    def scale_deployment(self, deployment: str, replicas: int) -> Dict[str, Any]:
        """Scales deployment replicas."""
        if self.backend == "python" and self.apps is not None:
            try:
                self.apps.patch_namespaced_deployment_scale(
                    deployment, self.namespace, {"spec": {"replicas": replicas}}
                )
                return {"success": True, "stdout": f"scaled {deployment} to {replicas}", "stderr": "", "exit_code": 0}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e), "exit_code": 1}
        return self.run_kubectl(["scale", f"deployment/{deployment}", f"--replicas={replicas}"])

    def delete_pod(self, pod_name: str) -> Dict[str, Any]:
        """Evicts a pod so replicaset creates a clean replacement."""
        if self.backend == "python" and self.core is not None:
            try:
                from kubernetes.client import V1DeleteOptions
                self.core.delete_namespaced_pod(
                    pod_name,
                    self.namespace,
                    body=V1DeleteOptions(grace_period_seconds=0, propagation_policy="Background"),
                )
                return {"success": True, "stdout": f"deleted {pod_name}", "stderr": "", "exit_code": 0}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e), "exit_code": 1}
        return self.run_kubectl(["delete", "pod", pod_name, "--grace-period=0", "--force"])
