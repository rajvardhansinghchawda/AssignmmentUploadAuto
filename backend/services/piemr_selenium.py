"""
PIEMR Portal Selenium Automation (v3 integrated)
Handles: login, navigation, question paper download, answer upload.
Target: accsoft.piemr.edu.in (ASP.NET WebForms)
"""
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoAlertPresentException,
    TimeoutException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

PORTAL_BASE = "https://accsoft.piemr.edu.in"
LOGIN_URL = f"{PORTAL_BASE}/Accsoft_PIEMR/studentLogin.aspx"
ASSIGNMENTS_URL = f"{PORTAL_BASE}/accsoft_piemr/Parents/Assignment.aspx"
WAIT_TIMEOUT = 15


# ── Utility ───────────────────────────────────────────────────────────────────

def _js_click(driver: webdriver.Chrome, el):
    """Scroll to element and JS-click to bypass ElementNotInteractableException"""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.1)
    driver.execute_script("arguments[0].click();", el)


def _dismiss_alert(driver: webdriver.Chrome, timeout=3) -> str:
    """Accept any open alert/confirm dialog. Returns alert text or empty string."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        txt = alert.text
        logger.info(f"[selenium] Alert dismissed: '{txt}'")
        alert.accept()
        return txt
    except (TimeoutException, NoAlertPresentException):
        return ""


# ── Driver ────────────────────────────────────────────────────────────────────

def build_driver(download_dir: str = None, headless: bool = True) -> webdriver.Chrome:
    """Build a configured Chrome WebDriver instance."""
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)

    if download_dir:
        os.makedirs(download_dir, exist_ok=True)
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        }
        opts.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(3)
    driver.set_page_load_timeout(60)
    logger.info("[selenium] Chrome WebDriver initialised")
    return driver


# ── Login ─────────────────────────────────────────────────────────────────────

def login(driver: webdriver.Chrome, enrollment_no: str, password: str, log_callback=None) -> bool:
    """Log into the PIEMR student portal."""
    msg = f"Logging in as {enrollment_no}"
    logger.info(f"[selenium] {msg}")
    if log_callback: log_callback(msg)
    
    driver.get(LOGIN_URL)
    time.sleep(2)

    # Multi-ID Username check (v3 compatibility)
    for uid in [
        "ctl00_ContentPlaceHolder1_txtUserName",
        "ctl00_ContentPlaceHolder1_txtEnrollNo",
        "txtUserName", "txtEnrollNo", "txtUsername",
    ]:
        try:
            f = driver.find_element(By.ID, uid)
            f.clear()
            f.send_keys(enrollment_no)
            break
        except NoSuchElementException:
            continue
    else:
        driver.find_element(By.XPATH, "(//input[@type='text'])[1]").send_keys(enrollment_no)

    # Password
    for pid in [
        "ctl00_ContentPlaceHolder1_txtPassword",
        "txtPassword", "txtPass",
    ]:
        try:
            f = driver.find_element(By.ID, pid)
            f.clear()
            f.send_keys(password)
            break
        except NoSuchElementException:
            continue
    else:
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(password)

    # Submit
    for bid in [
        "ctl00_ContentPlaceHolder1_btnLogin",
        "btnLogin", "btnSubmit",
    ]:
        try:
            driver.find_element(By.ID, bid).click()
            break
        except NoSuchElementException:
            continue
    else:
        driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']").click()

    time.sleep(3)
    _dismiss_alert(driver, timeout=2)

    if "Login" in driver.current_url or "studentLogin" in driver.current_url.lower():
        raise RuntimeError("Login failed — credentials may be incorrect")

    msg = "Login successful"
    logger.info(f"[selenium] {msg}")
    if log_callback: log_callback(msg)
    return True


# ── Navigation ────────────────────────────────────────────────────────────────

def open_assignments_page(driver: webdriver.Chrome, log_callback=None):
    """Navigate directly to the Assignments list page."""
    driver.get(ASSIGNMENTS_URL)
    time.sleep(2)
    _dismiss_alert(driver, timeout=2)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.dlTable"))
    )
    msg = "Navigated to assignments page"
    logger.info(f"[selenium] {msg}")
    if log_callback: log_callback(msg)


# ── Subject Scanning ──────────────────────────────────────────────────────────

def scan_subjects(driver: webdriver.Chrome, log_callback=None) -> list[dict]:
    """Scan the assignments page for subjects with pending assignments."""
    results = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table.dlTable tr")

    for row in rows:
        try:
            subject = row.find_element(By.XPATH, ".//span[contains(@id,'Label2')]").text.strip()
            new_count_str = row.find_element(By.XPATH, ".//input[contains(@id,'hdnNewACount')]").get_attribute("value")
            new_count = int(new_count_str) if new_count_str else 0
            if new_count > 0:
                link = row.find_element(By.XPATH, ".//a[contains(@id,'lnkViewNewAssign')]")
                results.append({
                    "name": subject,
                    "new_count": new_count,
                    "link_id": link.get_attribute("id"),
                })
                msg = f"Found open assignment: {subject} ({new_count} new)"
                logger.info(f"[selenium] {msg}")
                if log_callback: log_callback(msg)
        except Exception as e:
            logger.warning(f"[selenium] Row parse error: {e}")

    logger.info(f"[selenium] Found {len(results)} subjects")
    return results


# ── Download ──────────────────────────────────────────────────────────────────

def download_question_paper(driver: webdriver.Chrome, subject_info: dict, download_dir: str, assignment_index: int = 0, log_callback=None) -> str:
    """Find and download the question paper attachment. Returns local path."""
    os.makedirs(download_dir, exist_ok=True)
    existing_files = set(os.listdir(download_dir))

    # 1. Open assignments list and click the subject's link_id
    open_assignments_page(driver, log_callback=log_callback)
    link_id = subject_info.get("link_id")
    if not link_id:
        raise RuntimeError(f"No link_id in subject_info for {subject_info.get('name')}")
    
    link = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, link_id))
    )
    _js_click(driver, link)
    time.sleep(2)
    _dismiss_alert(driver, timeout=2)
    
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, "//tr[contains(@class,'GreenPage2')]"))
    )

    # 2. Find the target assignment row (avoid completed ones)
    rows = driver.find_elements(By.XPATH, "//tr[contains(@class,'GreenPage2')]")
    valid_rows = []
    
    for row in rows:
        try:
            btn = row.find_element(By.XPATH, ".//a[contains(@id,'btnUpload')]")
            # For testing: Allow re-upload
            valid_rows.append((row, btn.get_attribute("id")))
        except NoSuchElementException:
            continue

    if not valid_rows or assignment_index >= len(valid_rows):
        raise RuntimeError(f"No pending assignment row found at index {assignment_index} for {subject_info.get('name')}")

    target_row, target_btn_id = valid_rows[assignment_index]
    # Store the btn_id so `upload_file` targets the exactly same assigned row
    subject_info["target_btn_id"] = target_btn_id

    # 3. Handle Assignment Text (Show button)
    assignment_txt_path = None
    try:
        show_btn = target_row.find_element(By.XPATH, ".//input[@value='Show' or contains(@onclick, 'ShowAns')]")
        _js_click(driver, show_btn)
        time.sleep(1)
        onclick_attr = show_btn.get_attribute("onclick")
        ans_id = onclick_attr.split("'")[1] if "'" in onclick_attr else None
        
        if ans_id:
            ans_div = driver.find_element(By.ID, ans_id)
            assignment_text = ans_div.text.strip()
            if assignment_text:
                safe_name = subject_info.get('name', 'assignment').replace("/", "_").replace("\\", "_")
                txt_filename = f"{safe_name}_text.txt"
                assignment_txt_path = os.path.join(download_dir, txt_filename)
                with open(assignment_txt_path, "w", encoding="utf-8") as f:
                    f.write(assignment_text)
                logger.info(f"[selenium] Extracted assignment text to {txt_filename}")
    except Exception as e:
        logger.debug(f"[selenium] No Show button or text extraction failed: {e}")

    # 4. Find the download link
    download_clicked = False
    try:
        download_td = target_row.find_element(By.XPATH, ".//td[@data-label='Download Assignment']")
        download_links = download_td.find_elements(By.TAG_NAME, "a")
        
        # Click the link that isn't the javascript postback if it exists, otherwise fall back to any anchor
        for a in reversed(download_links):
            href = a.get_attribute("href") or ""
            if "javascript:" not in href:
                _js_click(driver, a)
                download_clicked = True
                break
        
        if not download_clicked and download_links:
            _js_click(driver, download_links[0])
            download_clicked = True
            
        if not download_clicked:
            logger.info("No anchors found in Download Assignment td")

    except NoSuchElementException:
        pass
        # Fallback to any file download links in the entire row
        if not download_clicked:
            links = target_row.find_elements(
                By.CSS_SELECTOR,
                "a[href*='.pdf'], a[href*='.docx'], a[href*='.doc'], a[download]"
            )
            if links:
                _js_click(driver, links[0])
                download_clicked = True

    if not download_clicked:
        if assignment_txt_path:
            logger.info(f"[selenium] No download found, but assignment text extracted for {subject_info.get('name')}")
            return assignment_txt_path
        else:
            raise RuntimeError(f"No question paper attachment or text found for {subject_info.get('name')}")

    logger.info(f"[selenium] Clicked download link for {subject_info.get('name')}")

    # 5. Wait for file to download
    timeout = 30
    elapsed = 0
    downloaded_path = None
    while elapsed < timeout:
        time.sleep(1)
        elapsed += 1
        current_files = set(os.listdir(download_dir))
        new_files = current_files - existing_files
        complete_files = [f for f in new_files if not f.endswith(".crdownload") and not f.endswith(".tmp")]
        if complete_files:
            # Favor the non-txt file if both are present
            non_txt = [f for f in complete_files if not f.endswith("_text.txt")]
            chosen = non_txt[0] if non_txt else complete_files[0]
            downloaded_path = os.path.join(download_dir, chosen)
            logger.info(f"[selenium] Downloaded: {downloaded_path}")
            break

    if not downloaded_path:
        if assignment_txt_path:
            msg = f"Download timed out, falling back to extracted text for {subject_info.get('name')}"
            logger.warning(msg)
            if log_callback: log_callback(msg)
            return assignment_txt_path
        raise RuntimeError(f"Download timed out for {subject_info.get('name')}")

    return downloaded_path


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_file(driver: webdriver.Chrome, subject_info: dict, file_path: str, log_callback=None) -> bool:
    """Upload the generated answer document to the PIEMR portal."""
    subject_name = subject_info.get("name", "unknown")
    target_btn_id = subject_info.get("target_btn_id")

    if not target_btn_id:
        # Failsafe: re-navigate if it wasn't populated (e.g. called out of order)
        open_assignments_page(driver, log_callback=log_callback)
        link = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, subject_info["link_id"]))
        )
        _js_click(driver, link)
        time.sleep(2)
        _dismiss_alert(driver, timeout=2)
        
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, "//tr[contains(@class,'GreenPage2')]"))
        )
        
        rows = driver.find_elements(By.XPATH, "//tr[contains(@class,'GreenPage2')]")
        for row in rows:
            try:
                btn = row.find_element(By.XPATH, ".//a[contains(@id,'btnUpload')]")
                # For testing: Allow re-upload
                target_btn_id = btn.get_attribute("id")
                break
            except NoSuchElementException:
                pass
        
    if not target_btn_id:
        raise RuntimeError(f"Could not find upload button for {subject_name}")

    logger.info(f"[selenium] Uploading answer doc for {subject_name}: {file_path}")

    # 1. Click the Upload anchor to open the modal
    upload_anchor = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, target_btn_id))
    )
    _js_click(driver, upload_anchor)
    time.sleep(2)
    _dismiss_alert(driver, timeout=1)

    # 2. Find file input
    file_input = None
    for _ in range(4):
        inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
        if inputs:
            file_input = inputs[0]
            break
        time.sleep(1)

    if not file_input:
        raise RuntimeError(f"No file input modal appeared for {subject_name}")

    # 3. Send keys to file input
    file_input.send_keys(os.path.abspath(file_path))
    time.sleep(1)

    # 4. Click Submit button in modal
    SUBMIT_XPATHS = [
        "//div[contains(@class,'modal-footer')]//button[not(contains(@class,'close') or contains(@class,'cancel'))]",
        "//div[contains(@class,'modal') and contains(@style,'block')]//input[@type='submit']",
        "//input[@type='submit' and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'upload')]",
        "//input[@type='submit' and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'upload')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
        "//a[contains(@class,'btn') and (contains(text(),'Upload') or contains(text(),'Submit') or contains(text(),'Save'))]",
    ]

    clicked = False
    for xp in SUBMIT_XPATHS:
        btns = driver.find_elements(By.XPATH, xp)
        if btns:
            _js_click(driver, btns[0])
            clicked = True
            msg = f"Clicked upload/submit button for {subject_name}"
            logger.info(f"[selenium] {msg}")
            if log_callback: log_callback(msg)
            break

    if not clicked:
        raise RuntimeError(f"Could not find submit button inside modal for {subject_name}")

    time.sleep(2)
    alert_text = _dismiss_alert(driver, timeout=4)
    if alert_text and ("success" in alert_text.lower() or "upload" in alert_text.lower()):
        logger.info("[selenium] Upload confirmed by alert")
    else:
        logger.info("[selenium] Upload submitted (no confirmation alert)")

    time.sleep(1)
    logger.info(f"[selenium] Upload complete for {subject_name}")
    return True
