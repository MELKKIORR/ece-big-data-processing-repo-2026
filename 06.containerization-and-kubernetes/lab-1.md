# Lab: Kubernetes basics with minikube

Basic manipulation with Kubernetes commands.

## Objectives

1. Install minikube
2. Learn to use `kubectl` commands
3. Learn to expose a Kubernetes service to the outside
4. Learn to scale up and down a Kubernetes deployment
5. Perform and roll back a rolling update
6. Deploy an app using manifest yaml files

## 1. Install minikube

[Install minikube](https://minikube.sigs.k8s.io/docs/start/) following the instructions depending on your OS (you may
skip the "Deploy applications" step).

Start minikube with:

```bash
minikube start
```

Verify global status of cluster:

```bash
minikube status
kubectl get nodes
kubectl describe node minikube
```

Activate metrics server and show the resources consumption. The metrics are available after a minute or so.

```bash
minikube addons enable metrics-server
```

Observe and explain what the command below does.

```bash
kubectl top pods -A --sort-by cpu --sum=true
```

Explore `kube-system` namespace and understand the role of each component by reading the [Kubernetes components
overview](https://kubernetes.io/docs/concepts/overview/components/).

```bash
kubectl -n kube-system get pods
```

## 2. Learn to use `kubectl` commands

1. Open a terminal

2. Run a `deployment` with one `pod` with the following command:

   ```bash
   kubectl create deployment kubernetes-bootcamp --image=gcr.io/google-samples/kubernetes-bootcamp:v1
   ```

   `gcr.io/google-samples/kubernetes-bootcamp:v1` is a Docker image of a basic Node.js web application.

   **NOTE!** You may need to install `kubectl` following the
   [instructions](https://kubernetes.io/docs/tasks/tools/#kubectl). This is not strictly necessary and you may
   substitute `kubectl` with `minikube kubectl --` if preferred.

3. List all the running pods with:

   ```bash
   kubectl get pods
   ```

   Wait until Pod readiness reaches 1/1 and save the Pod name in the environment variable `$POD_NAME`:

   ```bash
   export POD_NAME=$(kubectl get pods -l app=kubernetes-bootcamp -o jsonpath='{.items[0].metadata.name}')
   echo "$POD_NAME"
   ```

4. Display the pod logs and get more info:

   ```bash
   kubectl logs $POD_NAME
   kubectl describe pod $POD_NAME
   ```

5. Run a command inside the pod with:

   ```bash
   kubectl exec $POD_NAME -- cat /etc/os-release
   ```

6. Open a shell inside the pod with:

   ```bash
   kubectl exec -it $POD_NAME -- bash
   ```

7. List the content of the directory you are in and try to find the JavaScript source code file.

8. Make sure that the web app is responding inside the container by querying it with `curl`.

   > **Hint.** The port on which the app responds is defined in the `/server.js` JavaScript file

9. Exit the shell with `exit`. Are you able to query the web app outside of the pod (from your local machine)?

## 3. Learn to expose a Kubernetes service outside the minikube cluster

1. Expose the deployment you created in the first part of the lab with:

   ```bash
   kubectl expose deployments/$DEPLOYMENT_NAME --type="NodePort" --port $PORT_NUMBER
   ```

   > **Hint.** You need to replace `$DEPLOYMENT_NAME` with the actual name of the `deployment` as well as `$PORT_NUMBER`

2. Find out which port the service has been attached with:

   ```bash
   kubectl get services
   ```

3. Get the IP of your minikube node with:

   ```bash
   minikube ip
   ```

4. Using the answers of questions 2 and 3, open your web browser and try to reach the web app.

   > **Note!** If you are using the Docker driver (the default on most systems), the node IP is not reachable from your
   > machine. Create a tunnel to the service instead, replacing `$SERVICE_NAME` with your service name. The command
   > prints the URL to use and must stay running.
   >
   > ```bash
   > minikube service $SERVICE_NAME --url
   > ```

5. Save the URL of the web app in an environment variable, it is used in the next parts:

   ```bash
   export APP_URL="http://<ip>:<port>"
   curl "$APP_URL"
   ```

## 4. Learn to scale up and down a Kubernetes deployment

1. Scale up your deployment to a total number of 5 pods with:

   ```bash
   kubectl scale deployments/kubernetes-bootcamp --replicas=5
   ```

2. Make sure that you have 5 pods running using one of the commands we have seen in part 2 of the lab. Which command did
   you use?

3. Query the service several times. The response contains the name of the pod which served the request. What is
   happening? Why?

   ```bash
   for i in $(seq 10); do curl -s "$APP_URL"; done
   ```

   > **Note.** Load balancing is performed per connection. A web browser reuses the same connection and usually keeps
   > hitting the same pod, which is why `curl` is used here.

4. Scale down again your deployment to 2 pods and confirm the other 3 are not running anymore.

## 5. Perform and roll back a rolling update

1. In a second terminal, query the service in a loop and keep it running during the update:

   ```bash
   while true; do curl -s "$APP_URL"; sleep 0.5; done
   ```

2. Update the Docker image used by the `deployment` with:

   ```bash
   kubectl set image deployments/kubernetes-bootcamp kubernetes-bootcamp=jocatalin/kubernetes-bootcamp:v2
   ```

3. What happened to the responses? Was the service interrupted? Check the rollout with:

   ```bash
   kubectl rollout status deployments/kubernetes-bootcamp
   ```

4. Update the Docker image used by the `deployment` again by setting the image to `jocatalin/kubernetes-bootcamp:v3`.
   This tag does not exist on purpose.

5. List all the running pods, what is happening here? Is the service still responding? Why?

6. Cancel the previous operation by running:

   ```bash
   kubectl rollout undo deployments/kubernetes-bootcamp
   ```

7. Roll back the service to the image we first chose in part 2 of the lab. Look at `kubectl rollout history` and
   `kubectl rollout undo --help` to find how.

8. Stop the loop in the second terminal with `Ctrl+C`.

## 6. Deploy an app using manifest yaml files

1. Clean up what you did in the previous part with:

   ```bash
   kubectl delete service $SERVICE_NAME
   kubectl delete deployment $DEPLOYMENT_NAME
   ```

2. Move into the [`lab-1`](./lab-1/) directory which contains the manifests to complete:

   ```bash
   cd lab-1
   ```

3. Using the [deployment documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), fill out
   the blank (`TO COMPLETE #1`) in [`deployment.yaml`](./lab-1/deployment.yaml) to define a deployment based on the one
   we ran in part 2.

4. Once you completed the file, run:

   ```bash
   kubectl apply -f deployment.yaml
   ```

   Are the pods running?

5. Using the [service documentation](https://kubernetes.io/docs/concepts/services-networking/service/), fill out the
   blanks in [`service.yaml`](./lab-1/service.yaml)

6. Once you completed the file, run:

   ```bash
   kubectl apply -f service.yaml
   ```

   Can you access the service through `curl` or your web browser?

7. Fill out `TO COMPLETE #2` inside [`deployment.yaml`](./lab-1/deployment.yaml) to create 3 replicas of your app.

8. Once you completed the file, run:

   ```bash
   kubectl apply -f deployment.yaml
   ```

   Query the service several times. Are you hitting different replicas?

## 7. Teardown

Remove every workload deployed in this lab, then stop minikube.

```bash
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
minikube stop
```
