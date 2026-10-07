# Flask Todo App — Jenkins CI/CD Pipeline

A Flask todo web app with a fully automated CI/CD pipeline using Jenkins, Selenium, and Docker.

## What it does

Every push to `main` triggers Jenkins (via Poll SCM every minute) to automatically:

1. Run **unit tests** (`test_app.py`) — 3 tests, no browser
2. Run **Selenium UI tests** (`test_selenium.py`) — 10 tests in headless Chrome
3. Generate a **custom HTML test report** (`selenium_report.html`)
4. Build a **Docker image** and push it to Docker Hub

## Project structure

```
app.py                 Flask application
templates/index.html   UI template
Dockerfile             Container definition
Jenkinsfile            7-stage CI/CD pipeline
requirements.txt       Python dependencies

test_app.py            Unit tests (Flask test client)
test_selenium.py       Selenium end-to-end browser tests
conftest.py            pytest plugin — writes test_results.json
start_flask.py         Starts Flask in background, waits for port 5000
stop_flask.py          Stops Flask via PID file
generate_report.py     Builds selenium_report.html from test_results.json
```

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Unit tests
pytest test_app.py -v

# Selenium tests (starts/stops Flask automatically via Jenkins)
# Or run manually:
python start_flask.py
pytest test_selenium.py -v
python stop_flask.py
python generate_report.py
```

## Pipeline stages

| # | Stage | What happens |
|---|---|---|
| 1 | Checkout | Pulls latest code from GitHub |
| 2 | Setup | `pip install -r requirements.txt` |
| 3 | Unit Tests | 3 Flask route tests |
| 4 | Selenium UI Tests | 10 headless Chrome tests + HTML report |
| 5 | Docker Login | Authenticates to Docker Hub |
| 6 | Build Docker Image | `docker build` tagged with build number |
| 7 | Push Docker Image | Pushes `kurinoxd/flask-todo-app:<build#>` and `:latest` |

## Docker Hub

Image: [`kurinoxd/flask-todo-app`](https://hub.docker.com/r/kurinoxd/flask-todo-app)

```bash
docker pull kurinoxd/flask-todo-app:latest
docker run -p 5000:5000 kurinoxd/flask-todo-app:latest
```
