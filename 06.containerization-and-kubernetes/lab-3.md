# Lab: Job and CronJob

Explore Kubernetes Job & CronJob for task/compute execution.

## Objectives

By the end of this lab, you will be able to:

- Understand the difference between Job and CronJob
- Create and monitor Kubernetes Jobs
- Schedule recurring tasks with CronJob
- Apply Jobs and CronJobs to data pipeline scenarios (batch ETL, backups)
- Handle job failures and retries

## Prerequisites

- A running Kubernetes cluster (minikube)
- Familiarity with Pods and basic `kubectl` commands

## Job vs CronJob

Job: Runs a container to completion, retries on failure, stops when done.  
CronJob: Schedules Jobs using cron expressions (`0 2 * * *` = 2 AM daily).

Read the [Job and CronJob section of the course](./index.md#kubernetes-objects-job-and-cronjob) and check [crontab
guru](https://crontab.guru/examples.html) to experiment with cron expressions.

All the examples use the `python:3.13-slim` image. Pull it once before starting so that image download time does not
interfere with the Job deadlines:

```bash
minikube image pull python:3.13-slim
```

## Setup

Create lab namespace and directory.

```bash
kubectl create namespace lab-job-cronjob
mkdir lab-job-cronjob && cd lab-job-cronjob
```

## 1. Creating a Simple Job

Simple Job that runs a few Python print commands.

```bash
cat > job-simple.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: data-import-job
  namespace: lab-job-cronjob
spec:
  template:
    spec:
      containers:
      - name: import
        image: python:3.13-slim
        command: ["python", "-c"]
        args:
          - |
            import time
            print("Starting data import...")
            time.sleep(3)
            print("Processing 1000 records...")
            print("Import completed!")
      restartPolicy: Never
EOF

kubectl apply -f job-simple.yaml
kubectl -n lab-job-cronjob get job
kubectl -n lab-job-cronjob wait --for=condition=complete job/data-import-job --timeout=60s
kubectl -n lab-job-cronjob logs -l job-name=data-import-job
```

### Job with retry logic

The following Job simulates a transformation which always fails its validation. Kubernetes creates a new Pod for each
retry, waiting longer between each attempt (exponential back-off), until `backoffLimit` is reached.

```bash
cat > job-with-retry.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: data-transform-job
  namespace: lab-job-cronjob
spec:
  backoffLimit: 3          # 1 initial attempt + 3 retries
  activeDeadlineSeconds: 300
  template:
    spec:
      containers:
      - name: transform
        image: python:3.13-slim
        command: ["python", "-c"]
        args:
          - |
            import sys
            print("Transforming records...")
            print("ERROR: Validation failed!")
            sys.exit(1)
      restartPolicy: Never
EOF

kubectl apply -f job-with-retry.yaml
kubectl -n lab-job-cronjob get pods -l job-name=data-transform-job -w  # Ctrl+C once 4 pods are in Error
kubectl -n lab-job-cronjob describe job data-transform-job
```

Questions:

- How many Pods were created? Why are they kept after the failure?
- What is the reason of the Job failure in the `describe` output?
- Change `activeDeadlineSeconds` to `10`, delete and re-apply the Job. What is the new reason of the failure?

## 2. Job Parallelization

Launch a Job which processes 4 shards of a dataset in 4 Pods running in parallel. With `completionMode: Indexed`, each
Pod receives a distinct index in the `JOB_COMPLETION_INDEX` environment variable, used to select the shard to process.

```bash
cat > job-parallel.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-export-job
  namespace: lab-job-cronjob
spec:
  parallelism: 4            # Run 4 Pods in parallel
  completions: 4            # Need 4 successful completions
  completionMode: Indexed   # Completion index 0 to 3, one per Pod
  backoffLimit: 2
  ttlSecondsAfterFinished: 600  # Delete the Job and its Pods 10 minutes after completion
  template:
    spec:
      containers:
      - name: export
        image: python:3.13-slim
        command: ["python", "-c"]
        args:
          - |
            import os, time
            pod = os.getenv('HOSTNAME', 'unknown')
            shard = int(os.environ['JOB_COMPLETION_INDEX'])
            print(f"Pod {pod}: Exporting shard {shard} (users with id % 4 == {shard})...")
            time.sleep(5)
            print(f"Pod {pod}: Shard {shard} export completed!")
      restartPolicy: Never
EOF

kubectl apply -f job-parallel.yaml
kubectl -n lab-job-cronjob get pods -l job-name=batch-export-job -w  # Watch Pods run in parallel, Ctrl+C to stop
kubectl -n lab-job-cronjob logs -l job-name=batch-export-job --prefix
```

## 3. Creating a CronJob

CronJob that runs every 2 minutes.

```bash
cat > cronjob-pipeline.yaml << 'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: bronze-to-silver-pipeline
  namespace: lab-job-cronjob
spec:
  schedule: "*/2 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: transform
            image: python:3.13-slim
            command: ["python", "-c"]
            args:
              - |
                from datetime import datetime
                print(f"[{datetime.now()}] Bronze→Silver ETL started...")
                import time; time.sleep(2)
                print(f"[{datetime.now()}] Completed! 500 records processed")
          restartPolicy: Never
EOF

kubectl apply -f cronjob-pipeline.yaml
kubectl -n lab-job-cronjob get cronjob
kubectl -n lab-job-cronjob get jobs -w  # Watch Jobs created automatically, Ctrl+C to stop
```

Jobs created by a CronJob are named after the CronJob with a suffix, for example `bronze-to-silver-pipeline-29305920`.
Replace `<job-name>` with the name of one of the Jobs listed above to read its logs:

```bash
kubectl -n lab-job-cronjob logs job/<job-name>
```

### Common cron schedules for data pipelines

The cron format is `minute hour day-of-month month day-of-week`.

| Schedule       | Meaning                          | Typical usage                  |
| -------------- | -------------------------------- | ------------------------------ |
| `*/15 * * * *` | Every 15 minutes                 | Micro-batch ingestion          |
| `0 * * * *`    | Every hour, at minute 0          | Hourly aggregations            |
| `0 2 * * *`    | Every day at 2 AM                | Nightly ETL, backups           |
| `0 3 * * 1`    | Every Monday at 3 AM             | Weekly reports                 |
| `0 4 1 * *`    | The first day of every month     | Monthly archiving, compaction  |

Without the `timeZone` field, the schedule is interpreted in the time zone of the Kubernetes controller manager, usually
UTC.

```bash
# Example: Apply a nightly backup CronJob
cat > cronjob-backup.yaml << 'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
  namespace: lab-job-cronjob
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  timeZone: Europe/Paris
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: python:3.13-slim
            command: ["python", "-c", "print('Backup completed')"]
          restartPolicy: Never
EOF

kubectl apply -f cronjob-backup.yaml
```

## 4. Monitoring Jobs & CronJobs

```bash
# List all Jobs
kubectl -n lab-job-cronjob get jobs

# View Job status and events
kubectl -n lab-job-cronjob describe job data-import-job

# View logs from Job Pod
kubectl -n lab-job-cronjob logs -l job-name=data-import-job

# Suspend/resume a CronJob
kubectl -n lab-job-cronjob patch cronjob bronze-to-silver-pipeline -p '{"spec":{"suspend":true}}'
kubectl -n lab-job-cronjob patch cronjob bronze-to-silver-pipeline -p '{"spec":{"suspend":false}}'
```

## 5. Data Pipeline Scenario

This scenario combines the objects of the previous labs: the pipeline parameters are stored in a ConfigMap and injected
into the Pods of a CronJob.

```bash
kubectl -n lab-job-cronjob create configmap etl-config \
  --from-literal=BATCH_SIZE=1000 \
  --from-literal=SOURCE_LAYER=bronze \
  --from-literal=TARGET_LAYER=silver

cat > cronjob-etl.yaml << 'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etl-bronze-to-silver
  namespace: lab-job-cronjob
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 3600
      template:
        spec:
          containers:
          - name: etl
            image: python:3.13-slim
            envFrom:
            - configMapRef:
                name: etl-config
            resources:
              requests:
                cpu: 100m
                memory: 64Mi
              limits:
                memory: 128Mi
            command: ["python", "-c"]
            args:
              - |
                from datetime import datetime
                import os
                timestamp = datetime.now().isoformat()
                source, target = os.environ['SOURCE_LAYER'], os.environ['TARGET_LAYER']
                print(f"[{timestamp}] ETL: {source} -> {target}")
                print(f"[{timestamp}] Batch size: {os.environ['BATCH_SIZE']}")
                print(f"[{timestamp}] Reading, validating, deduplicating...")
                print(f"[{timestamp}] Writing to {target} layer...")
                print(f"[{timestamp}] Completed!")
          restartPolicy: Never
EOF

kubectl apply -f cronjob-etl.yaml
kubectl get cronjob -n lab-job-cronjob
kubectl get jobs -n lab-job-cronjob -w  # Ctrl+C to stop
```

To test the CronJob without waiting for its schedule, create a Job from its template:

```bash
kubectl -n lab-job-cronjob create job etl-manual-run --from=cronjob/etl-bronze-to-silver
kubectl -n lab-job-cronjob wait --for=condition=complete job/etl-manual-run --timeout=60s
kubectl -n lab-job-cronjob logs job/etl-manual-run
```

## Teardown

```bash
# Delete all Jobs and CronJobs in the namespace
kubectl -n lab-job-cronjob delete job --all
kubectl -n lab-job-cronjob delete cronjob --all

# Delete the namespace
kubectl delete namespace lab-job-cronjob

# Verify deletion
kubectl get namespace lab-job-cronjob  # Should show "not found"

# Remove lab directory
cd .. && rm -r lab-job-cronjob
```
