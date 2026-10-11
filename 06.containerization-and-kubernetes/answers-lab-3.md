# Lab 3 – Job and CronJob: answers

Environment: Windows 11, minikube (Docker driver), commands run in PowerShell. The manifests are in [`lab-3/`](./lab-3/).

## Job vs CronJob vs Deployment

| | Deployment | Job | CronJob |
| --- | --- | --- | --- |
| Purpose | Long-running service (web app, API) | Task that runs **to completion** (import, ETL, export) | Creates Jobs **on a schedule** (nightly ETL, backups) |
| End of the container | Restarted forever | Job is `Complete` once the required number of pods succeeded | Each run is a new Job |
| On failure | Pod restarted | New pod, up to `backoffLimit`, with exponential back-off | Depends on the Job template; `failedJobsHistoryLimit` keeps failed Jobs |

## 1. Simple Job

`data-import-job` creates one pod which prints `Starting data import...`, `Processing 1000 records...` and
`Import completed!`, then ends. The Job becomes `Complete 1/1` (duration 6s) and the pod `Completed`: it is not
restarted because `restartPolicy: Never` and the task succeeded.

### Job with retry logic

`data-transform-job` always exits with code 1.

- **How many pods were created? Why are they kept?** 4 pods (`8q8pr`, `klbtc`, `9nqvd`, `s2mhz`), all in `Error`:
  1 initial attempt + 3 retries (`backoffLimit: 3`). The creation times (2m31s, 2m20s, 2m, 80s) show the exponential
  back-off (about 10s, 20s, 40s between attempts). The failed pods are kept so that their logs and events can be
  inspected to debug the failure (`kubectl logs`, `kubectl describe pod`). They are deleted with the Job.
- **Reason of the failure in `describe`:** `BackoffLimitExceeded` (`Job has reached the specified backoff limit`).
- **With `activeDeadlineSeconds: 10`:** the Job is killed after 10 seconds, before reaching the backoff limit. The new
  reason is `DeadlineExceeded` (`Job was active longer than specified deadline`). Command used to apply the modified
  value without editing the file:

  ```powershell
  kubectl -n lab-job-cronjob delete job data-transform-job
  (Get-Content job-with-retry.yaml) -replace 'activeDeadlineSeconds: 300','activeDeadlineSeconds: 10' | kubectl apply -f -
  ```

  `activeDeadlineSeconds` takes precedence over `backoffLimit`: whichever limit is reached first fails the Job.

## 2. Job parallelization

`batch-export-job` (`parallelism: 4`, `completions: 4`, `completionMode: Indexed`): the 4 pods
`batch-export-job-0-...` to `batch-export-job-3-...` start at the same time and complete in about 10 seconds, so the
Job is `Complete 4/4` in 10s instead of about 4 × 5s sequentially. Each pod gets its own index in
`JOB_COMPLETION_INDEX` (also visible in the pod name) and processes a different shard:

```text
[pod/batch-export-job-0-z5nqv/export] Pod batch-export-job-0: Exporting shard 0 (users with id % 4 == 0)...
[pod/batch-export-job-1-n665c/export] Pod batch-export-job-1: Exporting shard 1 (users with id % 4 == 1)...
[pod/batch-export-job-2-tkx4q/export] Pod batch-export-job-2: Exporting shard 2 (users with id % 4 == 2)...
[pod/batch-export-job-3-zgp2t/export] Pod batch-export-job-3: Exporting shard 3 (users with id % 4 == 3)...
```

`ttlSecondsAfterFinished: 600` deletes the Job and its pods automatically 10 minutes after completion.

## 3. CronJob

`bronze-to-silver-pipeline` (`schedule: "*/2 * * * *"`) created a new Job every 2 minutes:
`bronze-to-silver-pipeline-29862310`, then `bronze-to-silver-pipeline-29862312`. The suffix is the scheduled time in
minutes since the Unix epoch, which is why it increases by 2. Each Job goes `Running` → `SuccessCriteriaMet` →
`Complete 1/1` in 5s.

- `concurrencyPolicy: Forbid`: a new run is skipped if the previous one is still running.
- `successfulJobsHistoryLimit: 3` / `failedJobsHistoryLimit: 1`: only the last 3 successful and the last failed Jobs are
  kept.

`daily-backup` (`0 2 * * *`, `timeZone: Europe/Paris`) runs every day at 2 AM Paris time: `kubectl get cronjob` shows
its `TIMEZONE` column and `LAST SCHEDULE <none>` since it has not run yet. Without `timeZone`, the schedule is
interpreted in the time zone of the controller manager (UTC).

## 4. Monitoring

- `kubectl -n lab-job-cronjob get jobs` lists the Jobs with their status, completions, duration and age.
- `kubectl -n lab-job-cronjob describe job <name>` shows the pods created, the conditions and the events.
- Suspending a CronJob (`patch ... {"spec":{"suspend":true}}`) sets `SUSPEND True`: no new Job is created until it is
  resumed with `suspend: false` (running Jobs are not affected). In PowerShell, the inner double quotes of the JSON
  patch must be escaped: `-p '{\"spec\":{\"suspend\":true}}'`.

## 5. Data pipeline scenario

The ConfigMap `etl-config` (`BATCH_SIZE=1000`, `SOURCE_LAYER=bronze`, `TARGET_LAYER=silver`) is injected into the pods
of the CronJob `etl-bronze-to-silver` with `envFrom`. A Job created manually from the CronJob template
(`kubectl create job etl-manual-run --from=cronjob/etl-bronze-to-silver`) runs it immediately:

```text
[2026-10-11T17:14:43.039922] ETL: bronze -> silver
[2026-10-11T17:14:43.039922] Batch size: 1000
[2026-10-11T17:14:43.039922] Reading, validating, deduplicating...
[2026-10-11T17:14:43.039922] Writing to silver layer...
[2026-10-11T17:14:43.039922] Completed!
```

The parameters come from the ConfigMap, so the pipeline can be reconfigured without changing the image or the
CronJob. The timestamps are in UTC (19:14 in Paris): containers run in UTC by default. The `resources` block reserves
100m CPU / 64Mi and limits memory to 128Mi, and `ttlSecondsAfterFinished: 3600` cleans finished Jobs after one hour.
