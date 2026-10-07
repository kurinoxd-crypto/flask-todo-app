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
APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"  # visible by default for demo

# ChromeDriver placed here manually to avoid webdriver-manager SYSTEM account bug
# Falls back to PATH if the file doesn't exist (e.g. on Linux CI)
CHROMEDRIVER_PATH = os.environ.get(
    "CHROMEDRIVER_PATH",
    r"C:\ProgramData\Jenkins\chromedriver\chromedriver-win32\chromedriver.exe"
)


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def driver():
    """Shared Chrome WebDriver for the entire test module."""
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-gpu")

    if os.path.exists(CHROMEDRIVER_PATH):
        service = Service(executable_path=CHROMEDRIVER_PATH)
    else:
        # Fallback: let Selenium find chromedriver on PATH
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
    time.sleep(0.8)  # brief pause so the demo is watchable


# ── Helper ────────────────────────────────────────────────────────────────────
def add_task(driver, text: str):
    """Fill the input and submit the Add Task form."""
    inp = driver.find_element(By.NAME, "task_content")
    inp.clear()
    inp.send_keys(text)
    driver.find_element(By.NAME, "add_task").click()
    # Wait for the task to appear in the list
    WebDriverWait(driver, 5).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
    )


# ── Tests ─────────────────────────────────────────────────────────────────────
class TestPageLoad:
    def test_title_is_todo_app(self, driver):
        """Page <title> should contain 'Todo'."""
        assert "Todo" in driver.title, f"Unexpected title: {driver.title}"

    def test_heading_visible(self, driver):
        """H1 heading should be present on the page."""
        h1 = driver.find_element(By.TAG_NAME, "h1")
        assert h1.is_displayed(), "H1 heading not visible"
        assert "Todo" in h1.text, f"Unexpected heading text: {h1.text}"

    def test_add_form_visible(self, driver):
        """The add-task form input and button should be visible."""
        inp = driver.find_element(By.NAME, "task_content")
        btn = driver.find_element(By.NAME, "add_task")
        assert inp.is_displayed()
        assert btn.is_displayed()


class TestAddTask:
    def test_add_single_task(self, driver):
        """Adding a task should display it in the list."""
        task_text = "Selenium test task"
        add_task(driver, task_text)
        body = driver.find_element(By.TAG_NAME, "body").text
        assert task_text in body, f"Task not found in page after adding: {body}"

    def test_add_multiple_tasks(self, driver):
        """Adding several tasks should display all of them."""
        tasks = ["Task Alpha", "Task Beta", "Task Gamma"]
        for t in tasks:
            add_task(driver, t)

        body = driver.find_element(By.TAG_NAME, "body").text
        for t in tasks:
            assert t in body, f"'{t}' missing from page"

    def test_empty_task_not_added(self, driver):
        """Submitting an empty task should not add a blank entry."""
        before = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        before_count = len(before)

        inp = driver.find_element(By.NAME, "task_content")
        inp.clear()
        driver.find_element(By.NAME, "add_task").click()
        time.sleep(0.5)

        after = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        assert len(after) == before_count, "Empty task was added to the list"


class TestDeleteTask:
    def test_delete_task(self, driver):
        """Deleting a task should remove it from the list."""
        task_text = "Task to be deleted via Selenium"
        add_task(driver, task_text)

        # Find the delete button next to our specific task
        items = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        target_item = None
        for item in items:
            if task_text in item.text:
                target_item = item
                break

        assert target_item is not None, "Could not find the task we just added"

        delete_btn = target_item.find_element(By.NAME, "delete_task")
        delete_btn.click()

        WebDriverWait(driver, 5).until(
            EC.staleness_of(target_item)
        )

        body = driver.find_element(By.TAG_NAME, "body").text
        assert task_text not in body, "Task still visible after deletion"

    def test_other_tasks_survive_deletion(self, driver):
        """Deleting one task must not remove other tasks."""
        add_task(driver, "Keep Me Around")
        add_task(driver, "Delete Me Only")

        items = driver.find_elements(By.CSS_SELECTOR, "li.task-item")
        for item in items:
            if "Delete Me Only" in item.text:
                item.find_element(By.NAME, "delete_task").click()
                break

        time.sleep(0.5)
        body = driver.find_element(By.TAG_NAME, "body").text
        assert "Keep Me Around" in body, "Unrelated task was removed during delete"
        assert "Delete Me Only" not in body, "Target task was not removed"


class TestUIDetails:
    def test_tasks_heading_present(self, driver):
        """'Tasks:' subheading should be visible."""
        h2 = driver.find_element(By.TAG_NAME, "h2")
        assert "Tasks" in h2.text

    def test_page_has_no_js_errors(self, driver):
        """Browser console should have no SEVERE JS errors (ignoring favicon 404)."""
        logs = driver.get_log("browser")
        severe = [
            l for l in logs
            if l.get("level") == "SEVERE"
            and "favicon.ico" not in l.get("message", "")
        ]
        assert severe == [], f"JS errors found: {severe}"
