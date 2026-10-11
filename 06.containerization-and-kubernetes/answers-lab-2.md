# Lab 2 – ConfigMap and Secret: answers

Environment: Windows 11, minikube (Docker driver), commands run in PowerShell. The manifests and files created during the
lab are in [`lab-2/`](./lab-2/). Bash-only commands were adapted to PowerShell (see below).

## ConfigMap vs Secret

| | ConfigMap | Secret |
| --- | --- | --- |
| Content | Non-sensitive configuration (paths, batch size, log level, config files) | Sensitive data (access keys, passwords, certificates) |
| Storage | Plain text in `data` | Base64-encoded in `data` (`stringData` lets you write plain values) |
| Protection | None | Base64 is **not** encryption: anyone with read access can decode it. Real protection comes from RBAC, encryption at rest in etcd, Sealed Secrets / External Secrets / Vault |

## 1. Creating ConfigMaps

Three methods were used, all in the namespace `lab-configmap-secret`:

1. `--from-file=pipeline-config.properties`: the whole file becomes **one key** named after the file
   (`pipeline-config.properties`) whose value is the file content.
2. `--from-literal=bronze=... --from-literal=silver=... --from-literal=gold=...`: one key per literal value
   (`bronze`, `silver`, `gold`).
3. `kubectl apply -f configmap-data-platform.yaml`: declarative manifest, mixing simple keys (`log_level`,
   `spark_workers`, `batch_size`) and keys holding whole files (`application.yaml`, `table_mappings.csv`). This is the
   preferred method because the manifest can be versioned in git (GitOps).

A single key is read with jsonpath, the dot of a key name being escaped:
`-o jsonpath='{.data.log_level}'` returns `INFO`, `-o jsonpath='{.data.application\.yaml}'` returns the YAML file.

## 2. Creating Secrets

Same three methods: `--from-literal` (`ceph-credentials`), `--from-file` (`s3-credentials`) and a manifest with
`stringData` (`ceph-s3-credentials`).

In `kubectl get secret ... -o yaml`, the values appear base64-encoded (e.g. `access-key: QUtJQUlPU0ZPRE5ON0VYQU1QTEU=`).
They are decoded without any key, which shows that base64 is only an encoding. PowerShell equivalent of
`base64 -d` / `jq`:

```powershell
$s = kubectl -n lab-configmap-secret get secret ceph-s3-credentials -o json | ConvertFrom-Json
$s.data.PSObject.Properties | ForEach-Object { "$($_.Name)=$([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_.Value)))" }
```

Output: `access-key=AKIAIOSFODNN7EXAMPLE`, `bucket=data-platform-bronze`, `endpoint=ceph-rgw...:7480`,
`secret-key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`.

> The credentials used in this lab are AWS documentation example keys, which give no access to anything. In a real
> project, `secret-ceph-credentials.yaml` and `s3-credentials.txt` must never be committed in clear text.

## 3. Using ConfigMaps and Secrets in Pods

### As environment variables

- `pod-with-configmap.yaml`: `LOG_LEVEL` and `SPARK_WORKERS` come from single keys (`configMapKeyRef`), and `envFrom`
  injects every key of `data-platform-config` as a variable. `env | Select-String "log_level|spark"` shows
  `LOG_LEVEL=INFO`, `SPARK_WORKERS=4`, `log_level=INFO`, `spark_workers=4`.
- `pod-with-secret.yaml`: `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ENDPOINT` come from `secretKeyRef`. The pod runs once
  (`restartPolicy: Never`) and its logs show `Access Key: AKIAIOSFODNN7EXAMPLE`. Printing a secret in logs is done for
  illustration only.

### As volumes (files)

- `pod-with-configmap-volume.yaml`: only the selected keys are mounted in `/etc/config` (`items`), and
  `table_mappings.csv` is renamed `tables.csv` through `path`. `cat` shows the full `application.yaml` and the CSV.
- `pod-with-secret-volume.yaml`: the Secret `s3-credentials` is mounted read-only in `/etc/ceph-credentials`.
  `ls -laL` shows `-rw------- root root 116 s3-credentials.txt`: the `defaultMode: 0600` gives read/write to the owner
  only. The `..data` and timestamped directories are symlinks used by Kubernetes to update the files atomically.

### Environment variables vs volumes

| | Environment variables | Volumes |
| --- | --- | --- |
| Use case | Simple scalar values | Whole files (YAML, CSV, certificates, credentials files) |
| Update | Fixed at container start: the pod must be restarted | Files are refreshed automatically when the ConfigMap/Secret changes (after a short delay) |
| Security | Visible in `env`, may leak in logs or crash dumps | File permissions (`defaultMode`), `readOnly` mount |

## Good practices for Secrets

- Mount secrets read-only with restrictive permissions (`readOnly: true`, `defaultMode: 0600`).
- Never print secrets in logs.
- Never commit plain Secret manifests: use Sealed Secrets, External Secrets Operator, Vault or a cloud secret manager.
- Restrict access with RBAC and enable encryption at rest of etcd.
