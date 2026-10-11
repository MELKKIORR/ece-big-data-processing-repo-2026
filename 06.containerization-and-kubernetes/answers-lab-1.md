# Lab 1 – Kubernetes basics with minikube: answers

Environment: Windows 11, minikube v1.39.0 (Docker driver), kubectl v1.34.1, commands run in PowerShell.

## 1. Install minikube

`kubectl top pods -A --sort-by cpu --sum=true` shows the CPU and memory consumption of every pod in **all namespaces**
(`-A`), sorted by CPU usage, with a **total** line at the end (`--sum=true`). It relies on the `metrics-server` addon
(right after enabling it, the command returns `Metrics API not available` until the metrics-server pod is ready).

Components of the `kube-system` namespace:

| Pod | Role |
| --- | --- |
| `kube-apiserver` | Entry point of the cluster: exposes the Kubernetes API, used by `kubectl` and every other component |
| `etcd` | Key-value store holding the whole state of the cluster |
| `kube-scheduler` | Chooses the node on which each new pod runs |
| `kube-controller-manager` | Runs the controllers (Deployment, ReplicaSet, Node...) that keep the actual state equal to the desired state |
| `kube-proxy` | Network rules on each node that implement Services (routing and load balancing to pods) |
| `coredns` | Internal DNS: resolves service names (e.g. `my-svc.my-ns.svc.cluster.local`) |
| `kindnet` | CNI network plugin used by minikube: gives pods an IP and lets them communicate |
| `storage-provisioner` | minikube addon that dynamically provisions volumes |
| `metrics-server` | Collects CPU/memory metrics of pods and nodes (used by `kubectl top` and autoscaling) |

## 2. kubectl commands

- 7. The source code is `/server.js`, at the root of the container filesystem.
- 8. The app listens on port **8080** (`www.listen(8080, ...)`). Inside the pod, `curl localhost:8080` returns
  `Hello Kubernetes bootcamp! | Running on: kubernetes-bootcamp-5cc66bcc9b-vlgv7 | v=1`.
- 9. No. From the local machine, `curl localhost:8080` fails (`Could not connect to server`): the pod only has an IP
  inside the cluster network. A Service is needed to expose it.

## 3. Expose the service

```bash
kubectl expose deployments/kubernetes-bootcamp --type="NodePort" --port 8080
```

- 2. `kubectl get services` shows `8080:30333/TCP`: the service is attached to NodePort **30333**.
- 3. `minikube ip` returns `192.168.49.2`.
- 4. With the Docker driver on Windows, the node IP is not reachable from the host, so a tunnel is required:
  `minikube service kubernetes-bootcamp --url` returns `http://127.0.0.1:49388`, and the app answers on this URL.

## 4. Scale up and down

- 2. `kubectl get pods` (or `kubectl get deployments`, which shows `5/5`).
- 3. The responses come from different pods (`hmj99`, `d5cvv`, `vlgv7`, `rj7wr`...). The Service **load balances**
  the connections between all the ready pods matching its selector `app=kubernetes-bootcamp`.
  Note: right after scaling, the new pods were still `ContainerCreating` and all requests went to the only ready pod: a
  Service only sends traffic to pods that are Ready.
- 4. After `kubectl scale deployments/kubernetes-bootcamp --replicas=2`, 3 pods go to `Terminating` then disappear,
  2 pods remain.

## 5. Rolling update and rollback

- 3. The responses switch progressively from `v=1` to `v=2` **without interruption**. Kubernetes performs a
  rolling update: it starts a new pod, waits until it is ready, then terminates an old one, and so on.
  `kubectl rollout status` ends with `deployment "kubernetes-bootcamp" successfully rolled out`.
- 5. The new pod is in `ErrImagePull` then `ImagePullBackOff` because the image `jocatalin/kubernetes-bootcamp:v3`
  does not exist (Kubernetes retries the pull with an increasing delay). The service **still responds with `v=2`**: an
  old pod is only removed once a new one is ready, so the two v2 pods keep serving the traffic. The rollout is blocked
  but the application is not broken.
- 6. `kubectl rollout undo deployments/kubernetes-bootcamp` removes the v3 pod.
- 7. `kubectl rollout history deployments/kubernetes-bootcamp` lists revisions 1, 3 and 4: revision 1 is v1, 3 is v3,
  4 is v2 (an undo re-applies the previous revision as a new one, so revision 2 became revision 4).
  Back to the first image:

  ```bash
  kubectl rollout undo deployments/kubernetes-bootcamp --to-revision=1
  ```

  The responses are `v=1` again.

## 6. Manifest files

Completed manifests: [`lab-1/deployment.yaml`](./lab-1/deployment.yaml) and [`lab-1/service.yaml`](./lab-1/service.yaml).

- 4. `kubectl apply -f deployment.yaml`: yes, the pod is `1/1 Running`.
- 6. `kubectl apply -f service.yaml` creates the NodePort service `kubernetes-bootcamp-service` (`8080:32495/TCP`).
  Through the tunnel (`minikube service kubernetes-bootcamp-service --url`), `curl` returns
  `Hello Kubernetes bootcamp! | Running on: kubernetes-bootcamp-576b7cbb77-s5wbk | v=1`.
- 8. With `replicas: 3`, `kubectl get pods` shows 3 running pods and 10 requests are served by the 3 different
  replicas (`s5wbk`, `vlvwt`, `xmcck`).
