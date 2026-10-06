import json

dashboard = {
  "annotations": { "list": [] },
  "editable": False,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 2,
  "id": None,
  "title": "SRE Real-Time Reliability and Auto-Remediation Monitor",
  "tags": ["sre", "realtime", "resilience"],
  "timezone": "browser",
  "schemaVersion": 38,
  "liveNow": True,
  "refresh": "1s",
  "time": {
    "from": "now-5m",
    "to": "now"
  },
  "timepicker": {
    "refresh_intervals": ["1s"],
    "time_options": ["1m", "2m", "5m", "15m"]
  },
  "panels": [
    # Row 1: 4 Core Health Indicators
    {
      "id": 1,
      "gridPos": { "h": 4, "w": 6, "x": 0, "y": 0 },
      "type": "stat",
      "title": "Real-Time Availability SLO %",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "clamp_max(clamp_min((sum(rate(http_requests_total{status=~\"2..\"}[10s])) / sum(rate(http_requests_total[10s]))) * 100, 0), 100)",
          "legendFormat": "Availability %"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "decimals": 2,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": None },
              { "color": "orange", "value": 98.0 },
              { "color": "green", "value": 99.9 }
            ]
          }
        }
      }
    },
    {
      "id": 2,
      "gridPos": { "h": 4, "w": 6, "x": 6, "y": 0 },
      "type": "stat",
      "title": "Live Request Throughput (RPS)",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "sum(rate(http_requests_total[10s]))",
          "legendFormat": "RPS"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps",
          "decimals": 1,
          "color": { "mode": "palette-classic" }
        }
      }
    },
    {
      "id": 3,
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
      "type": "stat",
      "title": "Live HTTP 5XX Error Rate %",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "clamp_max(clamp_min((sum(rate(http_requests_total{status=~\"5..\"}[10s])) / sum(rate(http_requests_total[10s]))) * 100, 0), 100)",
          "legendFormat": "5xx %"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "decimals": 2,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": None },
              { "color": "orange", "value": 1.0 },
              { "color": "red", "value": 2.0 }
            ]
          }
        }
      }
    },
    {
      "id": 4,
      "gridPos": { "h": 4, "w": 6, "x": 18, "y": 0 },
      "type": "stat",
      "title": "Real-Time System State",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "(sum(rate(http_requests_total{status=~\"5..\"}[10s])) > bool 0.1) or (histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[10s])) by (le)) > bool 1.2)",
          "legendFormat": "State"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "text": { "valueSize": 22, "titleSize": 14 },
          "mappings": [
            {
              "type": "value",
              "options": {
                "0": { "text": "HEALTHY", "color": "dark-green" },
                "1": { "text": "ACTIVE INCIDENT", "color": "dark-red" }
              }
            }
          ]
        }
      },
      "options": {
        "colorMode": "background",
        "graphMode": "none",
        "justifyMode": "center",
        "textMode": "value"
      }
    },

    # Row 2: Live Latency Timeseries & Ingress RPS vs 5xx Errors
    {
      "id": 5,
      "gridPos": { "h": 7, "w": 12, "x": 0, "y": 4 },
      "type": "timeseries",
      "title": "Real-Time Latency Profiles (p50, p95, p99)",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[10s])) by (le)) * 1000",
          "legendFormat": "p50 Latency (ms)"
        },
        {
          "datasource": "Prometheus",
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[10s])) by (le)) * 1000",
          "legendFormat": "p95 Latency (ms)"
        },
        {
          "datasource": "Prometheus",
          "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[10s])) by (le)) * 1000",
          "legendFormat": "p99 Latency (ms)"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "ms",
          "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth",
            "lineWidth": 2,
            "pointSize": 5,
            "showPoints": "auto"
          }
        }
      }
    },
    {
      "id": 6,
      "gridPos": { "h": 7, "w": 12, "x": 12, "y": 4 },
      "type": "timeseries",
      "title": "Live Ingress RPS vs 5XX Fault Errors",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "sum(rate(http_requests_total[10s]))",
          "legendFormat": "Total Throughput (RPS)"
        },
        {
          "datasource": "Prometheus",
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[10s]))",
          "legendFormat": "5xx Server Errors (EPS)"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "drawStyle": "line",
            "fillOpacity": 20,
            "lineWidth": 2
          }
        }
      }
    },

    # Row 3: Security Isolation Status & Live Service Traffic Share
    {
      "id": 7,
      "gridPos": { "h": 7, "w": 8, "x": 0, "y": 11 },
      "type": "stat",
      "title": "Agent Sandbox Security and Quarantine Status",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "sre_agent_sandbox_quarantine_status",
          "legendFormat": "Sandbox Status"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "text": { "valueSize": 20, "titleSize": 14 },
          "mappings": [
            {
              "type": "value",
              "options": {
                "0": { "text": "QUARANTINE LEAK DETECTED", "color": "dark-red" },
                "1": { "text": "SECURE IN SANDBOX (ISOLATED)", "color": "dark-green" }
              }
            }
          ]
        }
      },
      "options": {
        "colorMode": "background",
        "graphMode": "none",
        "justifyMode": "center",
        "textMode": "value"
      }
    },
    {
      "id": 10,
      "gridPos": { "h": 7, "w": 16, "x": 8, "y": 11 },
      "type": "piechart",
      "title": "Production Service Traffic Load Distribution",
      "description": "Real-time traffic split across microservice endpoints and upstream gateway routes.",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "sum by (endpoint) (rate(http_requests_total[1m]))",
          "legendFormat": "{{endpoint}}",
          "instant": True
        }
      ],
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": {
            "hideFrom": { "legend": False, "tooltip": False, "viz": False }
          }
        }
      },
      "options": {
        "reduceOptions": {
          "values": True,
          "calcs": ["lastNotNull"]
        },
        "pieType": "donut",
        "legend": {
          "displayMode": "table",
          "placement": "right",
          "showLegend": True,
          "values": ["value", "percent"]
        },
        "tooltip": {
          "mode": "single"
        }
      }
    },

    # Row 4: Full-Width Detailed Red Team Operations Table
    {
      "id": 8,
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 18 },
      "type": "table",
      "title": "Red Team Chaos Agent Operations (Live Audit Stream)",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "sre_agent_operation_events_total{squad=\"red-team\"}",
          "format": "table",
          "instant": True
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "align": "auto",
            "cellOptions": { "type": "auto" }
          }
        }
      },
      "transformations": [
        {
          "id": "labelsToFields",
          "options": { "mode": "columns" }
        },
        {
          "id": "organize",
          "options": {
            "excludeByName": {
              "Time": False,
              "__name__": True,
              "instance": True,
              "job": True,
              "squad": True,
              "detail": True,
              "action": True,
              "Value": True,
              "Value #A": True
            },
            "renameByName": {
              "agent": "Agent Name",
              "command": "Exact Command Executed",
              "result": "Exact Execution Result",
              "status": "State"
            },
            "indexByName": {
              "Time": 0,
              "agent": 1,
              "command": 2,
              "result": 3,
              "status": 4
            }
          }
        }
      ]
    },

    # Row 5: Full-Width Detailed Blue Team Operations Table
    {
      "id": 9,
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 26 },
      "type": "table",
      "title": "Blue Team SRE Agent Incident Response (Live Audit Stream)",
      "targets": [
        {
          "datasource": "Prometheus",
          "expr": "sre_agent_operation_events_total{squad=\"blue-team\"}",
          "format": "table",
          "instant": True
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "align": "auto",
            "cellOptions": { "type": "auto" }
          }
        }
      },
      "transformations": [
        {
          "id": "labelsToFields",
          "options": { "mode": "columns" }
        },
        {
          "id": "organize",
          "options": {
            "excludeByName": {
              "Time": False,
              "__name__": True,
              "instance": True,
              "job": True,
              "squad": True,
              "detail": True,
              "action": True,
              "Value": True,
              "Value #A": True
            },
            "renameByName": {
              "agent": "Agent Name",
              "command": "Exact Command Executed",
              "result": "Exact Execution Result",
              "status": "State"
            },
            "indexByName": {
              "Time": 0,
              "agent": 1,
              "command": 2,
              "result": 3,
              "status": 4
            }
          }
        }
      ]
    }
  ]
}

with open("dashboards/provisioning/dashboards/sre-dashboard.json", "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard rewritten: Pie chart is now 'Production Service Traffic Load Distribution' and tables show exact commands and results.")
