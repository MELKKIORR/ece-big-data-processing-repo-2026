# Lab: ConfigMap and Secret

Explore Kubernetes ConfigMap & Secret for storage of configuration and credentials.

## Objectives

By the end of this lab, you will be able to:

- Understand the difference between ConfigMap and Secret
- Create ConfigMaps and Secrets using `kubectl` and YAML manifests
- Inject ConfigMaps and Secrets into pod environment variables and volumes
- Store real-world credentials (S3 access keys, Ceph credentials)
- Apply basic security practices for sensitive data

## Prerequisites

- A running Kubernetes cluster (minikube)
- Familiarity with basic `kubectl` commands (from lab-1)
- `jq` installed

## Reminder

ConfigMaps store non-sensitive configuration, Secrets store sensitive data. Secret values are only base64-encoded, which
is not encryption. Read the [ConfigMap and Secret section of the
course](./index.md#kubernetes-objects-configmap-and-secret) before starting.

## 1. Setup

Create lab namespace and directory.

```bash
kubectl create namespace lab-configmap-secret
mkdir lab-configmap-secret && cd lab-configmap-secret
```

## 2. Creating ConfigMaps

### Method 1

Create ConfigMap from a file.

```bash
# Create a config file locally
cat > pipeline-config.properties << 'EOF'
# Data Pipeline Configuration
bronze.path=/mnt/data/bronze
silver.path=/mnt/data/silver
gold.path=/mnt/data/gold
batch.size=1000
retention.days=90
log.level=INFO
spark.cores=4
kafka.brokers=kafka-0.kafka.svc.cluster.local:9092
EOF

# Create ConfigMap from the file
kubectl -n lab-configmap-secret create configmap pipeline-config --from-file=pipeline-config.properties

# View the ConfigMap
kubectl -n lab-configmap-secret get configmap pipeline-config
kubectl -n lab-configmap-secret describe configmap pipeline-config
kubectl -n lab-configmap-secret get configmap pipeline-config -o yaml
```

### Method 2

Create ConfigMap from literal key-value pairs.

```bash
# Quick creation with direct values
kubectl -n lab-configmap-secret \
  create configmap data-paths \
  --from-literal=bronze=/mnt/data/bronze \
  --from-literal=silver=/mnt/data/silver \
  --from-literal=gold=/mnt/data/gold

# View it
kubectl -n lab-configmap-secret get configmap data-paths -o yaml
```

### Method 3

Create ConfigMap from YAML manifest. This is the preferred method for version control and GitOps.

```bash
# Create the YAML manifest
cat > configmap-data-platform.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-platform-config
  namespace: lab-configmap-secret
data:
  # Simple key-value pairs
  log_level: INFO
  spark_workers: "4"
  batch_size: "1000"

  # Multi-line config (entire file as a value)
  application.yaml: |
    # Data Platform Application Config
    pipeline:
      name: bronze-to-silver-etl
      schedule: "0 2 * * *"
      timeout_minutes: 120
    storage:
      type: s3
      endpoint: ceph-rgw.ceph-storage.svc.cluster.local:7480
      region: us-east-1
    kafka:
      bootstrap_servers: kafka-0.kafka.svc.cluster.local:9092
      consumer_group: data-platform-consumers
      topic_prefix: data.bronze

  # CSV mapping example
  table_mappings.csv: |
    source_table,bronze_path,silver_layer
    customers,/data/bronze/customers,deduplicated_customers
    orders,/data/bronze/orders,aggregated_orders
    products,/data/bronze/products,product_catalog
EOF

# Apply the ConfigMap
kubectl apply -f configmap-data-platform.yaml
```

### Inspect ConfigMap content

```bash
# View the entire ConfigMap
kubectl -n lab-configmap-secret get configmap data-platform-config -o yaml

# View specific key
kubectl -n lab-configmap-secret get configmap data-platform-config -o jsonpath='{.data.log_level}'

# View a file inside ConfigMap
kubectl -n lab-configmap-secret get configmap data-platform-config -o jsonpath='{.data.application\.yaml}'
```

## 3. Creating Secrets

### Method 1

Create Secret from literal values.

```bash
# Scenario: Store Ceph S3 credentials
kubectl -n lab-configmap-secret \
  create secret generic ceph-credentials \
  --from-literal=access-key=AKIAIOSFODNN7EXAMPLE \
  --from-literal=secret-key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# View it (note: data is encoded)
kubectl -n lab-configmap-secret get secret ceph-credentials -o yaml
```

### Method 2

Create Secret from a file.

```bash
# Create a credentials file locally (simulating a kubeconfig or cert)
cat > s3-credentials.txt << 'EOF'
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EOF

# Create Secret from file
kubectl -n lab-configmap-secret \
  create secret generic s3-credentials \
  --from-file=s3-credentials.txt

# View it
kubectl -n lab-configmap-secret get secret s3-credentials -o yaml
```

### Method 3

Create Secret from a YAML manifest. It is convenient to read and to apply, but the file contains the credentials in
clear text: it must not be committed as is.

**⚠️ WARNING:** base64 encoding does not protect a secret. In a real project, never commit a plain Secret manifest to
git: encrypt it with a tool like [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) or fetch it from a
vault.

```bash
# For this lab, we'll create it manually, but in production use:
# - Sealed Secrets (encrypts before committing)
# - External Secrets Operator (fetches from vault)
# - HashiCorp Vault
# - Cloud provider secret managers (Azure Key Vault, AWS Secrets Manager, GCP Secret Manager)

cat > secret-ceph-credentials.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: ceph-s3-credentials
  namespace: lab-configmap-secret
type: Opaque
stringData:  # Plain values, base64-encoded by the API server when the Secret is stored
  access-key: AKIAIOSFODNN7EXAMPLE
  secret-key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  endpoint: ceph-rgw.ceph-storage.svc.cluster.local:7480
  bucket: data-platform-bronze
EOF

# Apply the Secret
kubectl apply -f secret-ceph-credentials.yaml
```

### Decode Secret values

```bash
# Get the entire secret as YAML
kubectl -n lab-configmap-secret get secret ceph-s3-credentials -o yaml

# Manually decode one field
kubectl -n lab-configmap-secret get secret ceph-s3-credentials -o jsonpath='{.data.secret-key}' | base64 -d

# Decode all fields (requires jq 1.6 or later)
kubectl -n lab-configmap-secret \
  get secret ceph-s3-credentials -o json | \
  jq -r '.data | to_entries[] | "\(.key)=\(.value | @base64d)"'
```

## 4. Using ConfigMap & Secret in Pods

### Method 1

Inject as Environment Variables.

From ConfigMap

```bash
cat > pod-with-configmap.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: spark-app
  namespace: lab-configmap-secret
spec:
  containers:
  - name: app
    image: busybox:1.37
    command: ["sleep", "600"]
    env:
    # #1 ConfigMap key as env var
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: data-platform-config
          key: log_level

    # #2 ConfigMap key
    - name: SPARK_WORKERS
      valueFrom:
        configMapKeyRef:
          name: data-platform-config
          key: spark_workers

    # Inject all ConfigMap keys as env vars
    envFrom:
    - configMapRef:
        name: data-platform-config
EOF

kubectl apply -f pod-with-configmap.yaml

# Wait for the pod and verify env vars inside it
kubectl -n lab-configmap-secret wait --for=condition=Ready pod/spark-app --timeout=60s
kubectl -n lab-configmap-secret exec spark-app -- env | grep -iE "log_level|spark"
```

From Secret:

```bash
cat > pod-with-secret.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: ceph-connector
  namespace: lab-configmap-secret
spec:
  containers:
  - name: ceph-app
    image: busybox:1.37
    # The container runs once and exits: it must not be restarted
    command: ["sh", "-c", "echo \"Access Key: $S3_ACCESS_KEY\""]
    env:
    # Single Secret key as env var
    - name: S3_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: ceph-s3-credentials
          key: access-key

    - name: S3_SECRET_KEY
      valueFrom:
        secretKeyRef:
          name: ceph-s3-credentials
          key: secret-key

    - name: S3_ENDPOINT
      valueFrom:
        secretKeyRef:
          name: ceph-s3-credentials
          key: endpoint

    # Inject all Secret keys as env vars
    envFrom:
    - secretRef:
        name: ceph-s3-credentials
  restartPolicy: Never
EOF

kubectl apply -f pod-with-secret.yaml

# Wait for the pod to complete and view its logs.
# Printing credentials in logs is done here for illustration only: never do it in a real application.
kubectl -n lab-configmap-secret wait --for=jsonpath='{.status.phase}'=Succeeded pod/ceph-connector --timeout=60s
kubectl -n lab-configmap-secret logs ceph-connector
```

### Method 2

Mount as Volumes (Files)

From ConfigMap:

```bash
cat > pod-with-configmap-volume.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: spark-config-reader
  namespace: lab-configmap-secret
spec:
  containers:
  - name: app
    image: busybox:1.37
    command: ["sleep", "600"]
    volumeMounts:
    # Mount entire ConfigMap as a directory
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: data-platform-config
      # Optional: mount specific keys
      items:
      - key: application.yaml
        path: application.yaml  # File name inside /etc/config
      - key: table_mappings.csv
        path: tables.csv
EOF

kubectl apply -f pod-with-configmap-volume.yaml

# Wait for the pod, then view the mounted files
kubectl -n lab-configmap-secret wait --for=condition=Ready pod/spark-config-reader --timeout=60s
kubectl -n lab-configmap-secret exec spark-config-reader -- ls -la /etc/config/
kubectl -n lab-configmap-secret exec spark-config-reader -- cat /etc/config/application.yaml
kubectl -n lab-configmap-secret exec spark-config-reader -- cat /etc/config/tables.csv
```

From Secret:

```bash
cat > pod-with-secret-volume.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: ceph-connector-secure
  namespace: lab-configmap-secret
spec:
  containers:
  - name: ceph-app
    image: busybox:1.37
    command: ["sh", "-c", "sleep 1000"]
    volumeMounts:
    # Mount Secret as a volume (files)
    - name: ceph-creds
      mountPath: /etc/ceph-credentials
      readOnly: true  # Good practice: mount as read-only
  volumes:
  - name: ceph-creds
    secret:
      secretName: s3-credentials
      defaultMode: 0600  # File permissions (read/write for owner only)
EOF

kubectl apply -f pod-with-secret-volume.yaml

# Wait for the pod, then view the mounted credentials and their permissions
kubectl -n lab-configmap-secret wait --for=condition=Ready pod/ceph-connector-secure --timeout=60s
kubectl -n lab-configmap-secret exec ceph-connector-secure -- ls -laL /etc/ceph-credentials/
kubectl -n lab-configmap-secret exec ceph-connector-secure -- cat /etc/ceph-credentials/s3-credentials.txt
```

## Teardown

Remove every workload deployed in this lab.

```bash
kubectl delete namespace lab-configmap-secret
cd .. && rm -r lab-configmap-secret
```
