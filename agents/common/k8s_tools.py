import subprocess
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("sre-arena.k8s")

class K8sToolKit:
    def __init__(self, namespace: str = "sre-target-apps"):
        self.namespace = namespace
        self.k8s_available = self._check_kubectl()

    def _check_kubectl(self) -> bool:
        try:
            res = subprocess.run(["kubectl", "version", "--client", "-o", "json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def run_kubectl(self, args: List[str]) -> Dict[str, Any]:
        """Runs a kubectl command safely and returns output or error."""
        cmd = ["kubectl"] + args + ["-n", self.namespace]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "exit_code": res.returncode
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    def get_pods(self) -> List[Dict[str, Any]]:
        """Returns parsed list of pods and statuses."""
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
                    "labels": item["metadata"].get("labels", {})
                })
            return pods
        except Exception as e:
            logger.error(f"Error parsing pods: {e}")
            return []

    def get_recent_events(self, limit: int = 15) -> List[Dict[str, str]]:
        """Retrieves recent warning and error events in namespace."""
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
                    "object": f"{item.get('involvedObject', {}).get('kind', '')}/{item.get('involvedObject', {}).get('name', '')}"
                })
            return events
        except Exception:
            return []

    def get_pod_logs(self, pod_name: str, tail: int = 50) -> str:
        """Retrieves standard and previous logs of a pod."""
        res = self.run_kubectl(["logs", pod_name, f"--tail={tail}"])
        if res["success"]:
            return res["stdout"]
        # Try previous instance if pod restarted
        res_prev = self.run_kubectl(["logs", pod_name, f"--tail={tail}", "--previous"])
        if res_prev["success"]:
            return f"[PREVIOUS CONTAINER CRASH LOGS]:\n{res_prev['stdout']}"
        return res["stderr"]

    def rollout_undo(self, deployment: str) -> Dict[str, Any]:
        """Rolls back a deployment to previous revision."""
        return self.run_kubectl(["rollout", "undo", f"deployment/{deployment}"])

    def restart_deployment(self, deployment: str) -> Dict[str, Any]:
        """Performs rolling restart of deployment."""
        return self.run_kubectl(["rollout", "restart", f"deployment/{deployment}"])

    def scale_deployment(self, deployment: str, replicas: int) -> Dict[str, Any]:
        """Scales deployment replicas."""
        return self.run_kubectl(["scale", f"deployment/{deployment}", f"--replicas={replicas}"])

    def delete_pod(self, pod_name: str) -> Dict[str, Any]:
        """Evicts a pod so replicaset creates a clean replacement."""
        return self.run_kubectl(["delete", "pod", pod_name, "--grace-period=0", "--force"])
