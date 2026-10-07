"""
Selenium end-to-end tests for the Flask Todo App.

Requirements (add to requirements.txt or install manually):
    pip install selenium pytest-html webdriver-manager

The app must be running before these tests execute.
Set APP_URL env variable to override the default (http://localhost:5000).

Run:
    pytest test_selenium.py --html=selenium_report.html --self-contained-html -v
"""

import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Config ────────────────────────────────────────────────────────────────────
APP_URL  = os.environ.get("APP_URL", "http://localhost:5000")
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"

# DEMO_SPEED: seconds to pause between actions so the browser is watchable
# Set to 0 in CI (HEADLESS=true) for fast runs
DEMO_SPEED = 0.0 if HEADLESS else 1.2

CHROMEDRIVER_PATH = os.environ.get(
    "CHROMEDRIVER_PATH",
    r"C:\ProgramData\Jenkins\chromedriver\chromedriver-win32\chromedriver.exe"
)


# ── Helper ────────────────────────────────────────────────────────────────────
def pause(msg: str = ""):
    """Visible pause between actions during demo."""
    if msg and not HEADLESS:
        print(f"\n  >> {msg}")
    time.sleep(DEMO_SPEED)


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def driver():
    """Shared Chrome WebDriver for the entire test module."""
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")

    if os.path.exists(CHROMEDRIVER_PATH):
        service = Service(executable_path=CHROMEDRIVER_PATH)
    else:
        service = Service()

    drv = webdriver.Chrome(service=service, options=options)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


@pytest.fixture(autouse=True)
def go_home(driver):
    """Navigate to the home page before every test."""
    driver.get(APP_URL)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    pause("Loaded homepage")


# ── Helper ────────────────────────────────────────────────────────────────────
def add_task(driver, text: str):
    """Type into the input slowly then submit — visible during demo."""
    inp = driver.find_element(By.NAME, "task_content")
    inp.clear()

    # Type character by character so it's visible
    for char in text:
        inp.send_keys(char)
        time.sleep(0.06 if not HEADLESS else 0)

    pause(f"Typed: '{text}'")
    driver.find_element(By.NAME, "add_task").click()

    WebDriverWait(driver, 5).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
    )
    pause(f"Task added: '{text}'")


# ── Tests ─────────────────────────────────────────────────────────────────────
class TestPageLoad:
    def test_title_is_todo_app(self, driver):
        """Page title should contain 'Todo'."""
        pause("Checking page title...")
        assert "Todo" in driver.title, f"Unexpected title: {driver.title}"

    def test_heading_visible(self, driver):
        """H1 heading should be present and visible."""
        h1 = driver.find_element(By.TAG_NAME, "h1")
        pause(f"Found heading: '{h1.text}'")
        assert h1.is_displayed()
        assert "Todo" in h1.text

    def test_add_form_visible(self, driver):
        """The input box and Add Task button should be visible."""
        inp = driver.find_element(By.NAME, "task_content")
        btn = driver.find_element(By.NAME, "add_task")
        pause("Input and button are visible")
        assert inp.is_displayed()
        assert btn.is_displayed()


class TestAddTask:
    def test_add_single_task(self, driver):
        """Adding a task should display it in the list."""
        pause("-- TEST: Add a single task --")
        add_task(driver, "Buy groceries")
        body = driver.find_element(By.TAG_NAME, "body").text
        assert "Buy groceries" in body

    def test_add_multiple_tasks(self, driver):
        """Adding several tasks should display all of them."""
        pause("-- TEST: Add multiple tasks --")
        for task in ["Read a book", "Go for a walk", "Study Jenkins"]:
            add_task(driver, task)

        body = driver.find_element(By.TAG_NAME, "body").text
        for task in ["Read a book", "Go for a walk", "Study Jenkins"]:
            assert task in body

    def test_empty_task_not_added(self, driver):
        """Submitting empty input should not add a task."""
        pause("-- TEST: Try to add an empty task --")
        before = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        before_count = len(before)

        inp = driver.find_element(By.NAME, "task_content")
        inp.clear()
        pause("Clicking Add with empty input...")
        driver.find_element(By.NAME, "add_task").click()
        time.sleep(0.8)

        after = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        assert len(after) == before_count, "Empty task was added!"


class TestDeleteTask:
    def test_delete_task(self, driver):
        """Deleting a task should remove it from the list."""
        pause("-- TEST: Delete a task --")
        add_task(driver, "Task to delete")

        items = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        target = next((i for i in items if "Task to delete" in i.text), None)
        assert target is not None

        pause("Clicking Delete button...")
        target.find_element(By.NAME, "delete_task").click()

        WebDriverWait(driver, 5).until(EC.staleness_of(target))
        pause("Task deleted!")

        assert "Task to delete" not in driver.find_element(By.TAG_NAME, "body").text

    def test_other_tasks_survive_deletion(self, driver):
        """Deleting one task should not affect others."""
        pause("-- TEST: Only targeted task is deleted --")
        add_task(driver, "Keep this task")
        add_task(driver, "Delete this one")

        items = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        for item in items:
            if "Delete this one" in item.text:
                pause("Deleting 'Delete this one'...")
                item.find_element(By.NAME, "delete_task").click()
                break

        time.sleep(1)
        body = driver.find_element(By.TAG_NAME, "body").text
        assert "Keep this task" in body
        assert "Delete this one" not in body
        pause("Other task survived!")


class TestUIDetails:
    def test_tasks_heading_present(self, driver):
        """'Tasks:' subheading should be visible."""
        h2 = driver.find_element(By.TAG_NAME, "h2")
        pause(f"Found subheading: '{h2.text}'")
        assert "Tasks" in h2.text

    def test_page_has_no_js_errors(self, driver):
        """Browser console should have no SEVERE JS errors."""
        logs = driver.get_log("browser")
        severe = [
            l for l in logs
            if l.get("level") == "SEVERE"
            and "favicon.ico" not in l.get("message", "")
        ]
        pause("No JS errors found!" if not severe else f"JS errors: {severe}")
        assert severe == [], f"JS errors found: {severe}"
