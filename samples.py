# samples.py
# Three realistic sample log payloads for the Streamlit dropdown.

SAMPLES = {
    "OOMKilled / Exit Code 137": """\
State:          Terminated
  Reason:       OOMKilled
  Exit Code:    137
  Started:      Mon, 15 Jan 2024 14:23:01 +0000
  Finished:     Mon, 15 Jan 2024 14:25:44 +0000
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
Restart Count:  8

Limits:
  memory:   512Mi
Requests:
  memory:   256Mi

Events:
  Warning  OOMKilling  3m  kernel   Memory cgroup out of memory: Kill process 12847
  Warning  BackOff     2m  kubelet  Back-off restarting failed container

2024-01-15T14:23:01Z WARN  app Heap usage at 94% — approaching limit
2024-01-15T14:24:10Z ERROR app java.lang.OutOfMemoryError: Java heap space
2024-01-15T14:25:44Z FATAL app oom_kill_process — container terminated
""",

    "CrashLoopBackOff": """\
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       Error
  Exit Code:    1
Restart Count:  15

Events:
  Warning  BackOff  30s  kubelet  Back-off restarting failed container
  Warning  BackOff  60s  kubelet  Back-off restarting failed container

2024-01-15T14:20:01Z ERROR app Failed to connect to database: connection refused (host=postgres:5432)
2024-01-15T14:20:02Z ERROR app FATAL: startup failed after 3 retries
2024-01-15T14:20:03Z ERROR app exit status 1
""",

    "CreateContainerConfigError": """\
State:          Waiting
  Reason:       CreateContainerConfigError

Events:
  Warning  Failed  5m  kubelet  Error: secret "db-credentials" not found
  Warning  Failed  4m  kubelet  couldn't find key DB_PASSWORD in Secret default/db-credentials
  Warning  Failed  3m  kubelet  CreateContainerConfigError

Pod spec:
  envFrom:
    - secretRef:
        name: db-credentials
  env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: DB_PASSWORD

Namespace: production
""",
}
