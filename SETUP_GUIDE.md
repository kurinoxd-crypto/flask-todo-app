# Full Integration Setup Guide
### GitHub → Jenkins → Docker Hub → AWS EKS + Selenium Reports

---

## Before You Start — things you need

| What | Where to get it |
|---|---|
| GitHub account | github.com |
| Docker Hub account | hub.docker.com |
| AWS account | aws.amazon.com |
| Jenkins server (local or EC2) | See note below |
| Google Chrome installed on Jenkins node | For Selenium |

> **Jenkins on EC2 tip**: Launch a `t3.medium` Ubuntu EC2, open port 8080 in its security group, then install Jenkins with:
> ```bash
> sudo apt update && sudo apt install -y openjdk-17-jdk
> curl -fsSL https://pkg.jenkins.io/debian/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
> echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
> sudo apt update && sudo apt install -y jenkins
> sudo systemctl start jenkins
> ```

---

## Step 1 — Push your code to GitHub

```bash
# Inside jenkins-project folder
git init                          # skip if .git already exists
git add .
git commit -m "Initial commit"

# Create a new repo on github.com first, then:
git remote add origin https://github.com/kurinoxd-crypto/flask-todo-app.git
git branch -M main
git push -u origin main
```

### Add GitHub credentials to Jenkins
1. Jenkins → **Manage Jenkins** → **Credentials** → Global → **Add Credentials**
2. Kind: **Username with password**
3. Username: your GitHub username
4. Password: a GitHub **Personal Access Token** (Settings → Developer settings → PAT → Classic → check `repo`)
5. ID: `github-credentials-id`  ← this matches the Jenkinsfile exactly

---

## Step 2 — Docker Hub credentials in Jenkins

1. Jenkins → **Manage Jenkins** → **Credentials** → Global → **Add Credentials**
2. Kind: **Username with password**
3. Username: your Docker Hub username
4. Password: your Docker Hub password (or an access token from hub.docker.com → Account Settings → Security)
5. ID: `dockerhub-credentials-id`  ← matches the Jenkinsfile

### Update the Jenkinsfile
Open `Jenkinsfile` and replace:
```
DOCKERHUB_USERNAME = 'YOUR_DOCKERHUB_USERNAME'
```
with your actual Docker Hub username, e.g. `'harit123'`.

Also replace in `deployment.yaml`:
```
image: YOUR_DOCKERHUB_USERNAME/flask-todo-app:latest
```
with your username.

---

## Step 3 — AWS EKS cluster + kubeconfig credential

### 3a. Create the EKS cluster (one-time)
Follow `eksClusterCreation.md` in this repo — it walks through the full AWS console steps.

Quick summary:
```bash
# After cluster exists, get the kubeconfig
aws eks update-kubeconfig --name demo-eks --region us-east-1

# Verify
kubectl get nodes
```

### 3b. Store kubeconfig in Jenkins
1. On your machine: `cat ~/.kube/config` — copy the full content
2. Jenkins → **Manage Jenkins** → **Credentials** → Global → **Add Credentials**
3. Kind: **Secret file**
4. Upload your kubeconfig file (or paste into a temp file and upload)
5. ID: `kubeconfig-credentials-id`  ← matches the Jenkinsfile

### 3c. Install kubectl on the Jenkins server
```bash
sudo curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

---

## Step 4 — Install required Jenkins plugins

Go to **Manage Jenkins** → **Plugins** → Available plugins, search and install:

| Plugin | Why |
|---|---|
| **Git** | Clone from GitHub |
| **Docker Pipeline** | Build/push Docker images |
| **HTML Publisher** | Show Selenium report in Jenkins UI |
| **Pipeline** | Run Jenkinsfile pipelines |
| **Credentials Binding** | Inject secrets into shell steps |

Restart Jenkins after installing.

---

## Step 5 — Install Chrome on the Jenkins node (for Selenium)

```bash
# On the Jenkins server (Ubuntu/Debian)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable

# Verify
google-chrome --version
```

`webdriver-manager` in `requirements.txt` handles ChromeDriver automatically — no manual driver install needed.

---

## Step 6 — Create the Jenkins Pipeline job

1. Jenkins → **New Item** → name it `flask-todo-pipeline` → **Pipeline** → OK
2. Scroll to **Pipeline** section
3. Definition: **Pipeline script from SCM**
4. SCM: **Git**
5. Repository URL: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`
6. Credentials: `github-credentials-id`
7. Branch: `*/main`
8. Script Path: `Jenkinsfile`
9. **Save**

---

## Step 7 — Run the pipeline

Click **Build Now**. You will see these stages:

```
Checkout  →  Setup  →  Unit Tests  →  Selenium UI Tests
    →  Docker Login  →  Build Image  →  Push Image  →  Deploy to EKS
```

### View the Selenium HTML report
After the build finishes → click the build number → **Selenium Test Report** link in the left sidebar.

The report shows each test with pass/fail status, screenshots path, and error messages for any failures.

---

## Step 8 — Verify the deployment

```bash
# Check pods are running
kubectl get pods

# Get the external URL (wait ~2 min for LoadBalancer to provision)
kubectl get service flask-app-service

# Open the EXTERNAL-IP in your browser on port 80
# e.g. http://a1b2c3d4e5.us-east-1.elb.amazonaws.com
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `pytest` not found | Add `pip install pytest` to Setup stage or check virtualenv |
| `docker: command not found` | Install Docker on Jenkins node: `sudo apt install docker.io` then `sudo usermod -aG docker jenkins` |
| Selenium `SessionNotCreatedException` | Chrome not installed on Jenkins node — see Step 5 |
| `kubectl: connection refused` | KUBECONFIG credential file path wrong, or cluster endpoint not reachable from Jenkins |
| `ImagePullBackOff` in EKS | Docker image name in deployment.yaml doesn't match what was pushed |
| Port 5000 already in use (Selenium stage) | Add `pkill -f 'python app.py' || true` before `nohup python app.py` |

---

## How the Selenium tests work

`test_selenium.py` spins up a headless Chrome browser and tests the real running UI:

| Test class | What it checks |
|---|---|
| `TestPageLoad` | Title, H1 heading, form visible |
| `TestAddTask` | Add one task, add many, empty task rejected |
| `TestDeleteTask` | Delete removes target, others survive |
| `TestUIDetails` | "Tasks:" heading present, no JS console errors |

To run locally (with the app running in another terminal):
```bash
# Terminal 1
python app.py

# Terminal 2
HEADLESS=false APP_URL=http://localhost:5000 pytest test_selenium.py --html=selenium_report.html --self-contained-html -v
```

Set `HEADLESS=false` to watch the browser in real time on your local machine.
