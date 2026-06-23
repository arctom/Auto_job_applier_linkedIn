'''
Author:     Tom Arc
LinkedIn:   https://www.linkedin.com/in/tom-arc

Copyright (C) 2024 Tom Arc


'''


# Imports
import os
import csv
import re
import pyautogui

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException

from config.personals import *
from config.questions import *
from config.search import *
from config.secrets import use_AI, username, password
from config.settings import *

from modules.open_chrome import initialize_driver, driver, wait, actions
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config
from modules.ai.aiConnections import *
from modules.learned_answers import load_learned_answers, find_learned_answer, save_learned_answer, _similarity
from modules.resumes.extractor import get_user_profile

from typing import Literal


pyautogui.FAILSAFE = False


#< Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
userProfile = None
#>


#< Login Functions
def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    # If we're on the login page, user is definitely not logged in
    if "linkedin.com/login" in driver.current_url: return False
    buffer(2)  # Let the page render before hunting for elements
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    '''
    Function to login for LinkedIn
    * Uses JavaScript to generically find and fill form fields — no hardcoded selectors
    * Handles both the older single-page login and the newer two-step login flow
    * If auto-login fails, asks user to login manually
    '''
    driver.get("https://www.linkedin.com/login")
    buffer(3)

    try:
        # Step 1: Find and fill the username field using native DOM setter (bypasses React)
        fill_result = driver.execute_script("""
            const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            const inputs = document.querySelectorAll('input:not([type="hidden"])');
            for (const inp of inputs) {
                if (inp.type === 'text' || inp.type === 'email' || inp.autocomplete === 'username'
                    || inp.id === 'username' || inp.id === 'session_key' || inp.name === 'session_key') {
                    inp.focus();
                    nativeSetter.call(inp, '');
                    nativeSetter.call(inp, arguments[0]);
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                    inp.dispatchEvent(new FocusEvent('focus', {bubbles: true}));
                    inp.dispatchEvent(new FocusEvent('blur', {bubbles: true}));
                    // Verify the value stuck
                    return 'filled username: ' + (inp.id || inp.name) + ' value=[' + inp.value + ']';
                }
            }
            return 'no username field found. total inputs: ' + inputs.length;
        """, username)
        print_lg("Step1 (username): " + str(fill_result))
        buffer(1)

        # Step 2: Find and fill the password field
        pass_result = driver.execute_script("""
            const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            const inputs = document.querySelectorAll('input:not([type="hidden"])');
            for (const inp of inputs) {
                if (inp.type === 'password') {
                    inp.focus();
                    nativeSetter.call(inp, '');
                    nativeSetter.call(inp, arguments[0]);
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                    inp.dispatchEvent(new FocusEvent('focus', {bubbles: true}));
                    inp.dispatchEvent(new FocusEvent('blur', {bubbles: true}));
                    return 'filled password: ' + (inp.id || inp.name) + ' value=[' + inp.value + ']';
                }
            }
            return 'no password field found. total inputs: ' + inputs.length;
        """, password)
        print_lg("Step2 (password): " + str(pass_result))
        buffer(1)

        # Step 3: Submit — try multiple strategies
        submit_result = driver.execute_script("""
            // Strategy A: Click the actual Sign in button (not social SSO buttons)
            const allButtons = document.querySelectorAll('button, input[type="submit"], [role="button"]');
            for (const btn of allButtons) {
                const text = (btn.textContent || btn.value || btn.getAttribute('aria-label') || '').toLowerCase();
                const isSubmit = btn.type === 'submit';
                const isSso = text.includes('with apple') || text.includes('with google') || text.includes('with facebook');
                if (!isSso && (text.includes('sign in') || text.includes('next') || text.includes('agree') || isSubmit)) {
                    try { btn.click(); return 'clicked: ' + text.trim(); }
                    catch(e) { return 'click error: ' + e.message; }
                }
            }
            // Strategy B: Submit any form
            const forms = document.querySelectorAll('form');
            for (const f of forms) {
                try { f.submit(); return 'submitted form: ' + (f.id || f.action || 'unnamed'); }
                catch(e) { return 'form error: ' + e.message; }
            }
            // Strategy C: Press Enter on password field
            const pw = document.querySelector('input[type="password"]');
            if (pw) {
                ['keydown','keypress','keyup'].forEach(type => {
                    pw.dispatchEvent(new KeyboardEvent(type, {key:'Enter', code:'Enter', keyCode:13, which:13, bubbles:true, cancelable:true}));
                });
                return 'dispatched Enter on password field';
            }
            return 'all strategies failed. buttons:' + allButtons.length + ' forms:' + forms.length;
        """)
        print_lg("Step3 (submit): " + str(submit_result))

    except Exception as e1:
        print_lg("Exception during credential entry: {} - {}".format(type(e1).__name__, str(e1)[:200]))
        try:
            screenshot_path = logs_folder_path + "/screenshots/login_failure_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            driver.save_screenshot(screenshot_path)
            print_lg("Saved login failure screenshot to: " + screenshot_path)
        except Exception:
            pass
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            print_lg("Couldn't Login! (profile fallback also failed)")

    try:
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        manual_login_retry(is_logged_in_LN, 2)
#>



def get_applied_job_ids() -> set:
    '''
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    '''
    job_ids = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids



def set_search_location() -> None:
    '''
    Function to set search location
    '''
    if search_location.strip():
        try:
            print_lg(f'Setting search location as: "{search_location.strip()}"')
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code'and not(@disabled)]", False) #  and not(@aria-hidden='true')]")
            text_input(actions, search_location_ele, search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(driver, ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']")
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg("Failed to update search location, continuing with default location!", e)


def apply_filters() -> None:
    '''
    Function to apply job search filters
    '''
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="All filters"]'))).click()
        buffer(recommended_wait)

        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel(driver, experience_level) 
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies: buffer(recommended_wait)

        multi_sel(driver, job_type)
        multi_sel(driver, on_site)
        if job_type or on_site: buffer(recommended_wait)

        if easy_apply_only: boolean_button_click(driver, actions, "Easy Apply")
        
        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry: buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles: buffer(recommended_wait)

        if under_10_applicants: boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network: boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer: boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)
        
        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments: buffer(recommended_wait)

        show_results_button: WebElement = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]')
        show_results_button.click()

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm("These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.", "Please check your results", ["Turn off Pause after search", "Look's good, Continue"]):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        # print_lg(e)



def get_page_info() -> tuple[list[WebElement] | None, int | None]:
    '''
    Function to get pagination page buttons and current page number.
    Uses aria-label based selectors which are more stable than class names.
    Returns a list of page button WebElements and the current page number.
    '''
    try:
        page_buttons = driver.find_elements(By.XPATH, "//button[starts-with(@aria-label, 'Page ')]")
        if not page_buttons:
            # Fallback: try older class-based selectors
            try:
                pagination_element = try_find_by_classes(driver, ["artdeco-pagination", "artdeco-pagination__pages"])
                page_buttons = pagination_element.find_elements(By.XPATH, ".//button[starts-with(@aria-label, 'Page ')]")
            except Exception:
                print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
                return None, None
        current_page = None
        for btn in page_buttons:
            if btn.get_attribute("aria-current") == "true" or "active" in (btn.get_attribute("class") or ""):
                current_page = int(btn.get_attribute("aria-label").replace("Page ", ""))
                break
        if current_page is None:
            current_page = 1
        scroll_to_view(driver, page_buttons[-1])
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        print_lg(e)
        return None, None
    return page_buttons, current_page



def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    '''
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    '''
    job_details_button = job.find_element(By.TAG_NAME, 'a')  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute('data-occludable-job-id')
    title = job_details_button.text
    title = title[:title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
    index = other_details.find(' · ')
    company = other_details[:index]
    work_location = other_details[index+3:]
    work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
    work_location = work_location[:work_location.rfind('(')].strip()
    
    # Skip if previously rejected due to blacklist or already applied
    skip = False
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except Exception:
        pass  # Non-critical: element may not exist for all job cards
    try: 
        if not skip: job_details_button.click()
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!') 
        # print_lg(e)
        discard_job()
        job_details_button.click() # To pass the error outside
    buffer(click_gap)
    return (job_id,title,company,work_location,work_style,skip)


# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if re.search(r'\b' + re.escape(word) + r'\b', about_company, re.IGNORECASE):
            print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words:
            if re.search(r'\b' + re.escape(word) + r'\b', about_company, re.IGNORECASE):
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card



# Function to extract years of experience required from About Job
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0
    return max([int(match) for match in matches if int(match) <= 12])



def get_job_description(
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''
    try:
        jobDescription = "Unknown"
        experience_required = "Unknown"
        found_masters = 0
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        jobDescriptionLow = jobDescription.lower()
        skip = False
        skipReason = None
        skipMessage = None
        for word in bad_words:
            if re.search(r'\b' + re.escape(word) + r'\b', jobDescriptionLow, re.IGNORECASE):
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        if not skip:
            # AI-based job relevance check
            if use_AI and aiClient and min_relevance_score > 0:
                relevance = ai_check_job_relevance(aiClient, jobDescription, user_profile=userProfile)
                if relevance and relevance.get("relevance_score", 100) < min_relevance_score:
                    skipMessage = f'\n{jobDescription}\n\nAI relevance score {relevance.get("relevance_score", 0)} < {min_relevance_score}. Skipping this job!\nReasoning: {relevance.get("reasoning", "N/A")}'
                    skipReason = "Low AI relevance score"
                    skip = True
            if not skip and did_masters and 'master' in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if not skip and use_AI and aiClient and experience_required == 0:
                ai_exp = ai_gen_experience(aiClient, jobDescription, userProfile)
                if ai_exp and ai_exp.get("years_required", 0) > 0:
                    experience_required = ai_exp["years_required"]
                    print_lg(f"AI extracted experience: {experience_required} years")
            if not skip and current_experience > -1 and isinstance(experience_required, int) and experience_required > current_experience + found_masters:
                skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                skipReason = "Required experience is high"
                skip = True
    except Exception as e:
        if jobDescription == "Unknown":    print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    finally:
        return jobDescription, experience_required, skip, skipReason, skipMessage
        


# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(default_resume_path)
    except: return False, "Previous resume"

# Function to answer common questions for Easy Apply
def answer_common_questions(label: str, answer: str) -> str:
    if 'sponsorship' in label or 'visa' in label: answer = require_visa
    return answer


def capture_manual_answers(modal: WebElement) -> None:
    '''
    Scans all form fields in the modal and saves their current values
    as learned answers. Called after manual intervention so user edits persist.
    '''
    import re

    all_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    all_questions = all_questions + all_list_questions + all_single_line_questions

    for Question in all_questions:
        # Extract label text
        label_org = ""
        try:
            label_el = Question.find_element(By.TAG_NAME, "label")
            span = try_xp(label_el, ".//span", False)
            label_org = span.text.strip() if span else label_el.text.strip()
        except Exception:
            pass
        if not label_org:
            # Try aria-label or data-test attributes
            label_el = try_xp(Question, ".//*[@aria-label]", False)
            if label_el:
                label_org = label_el.get_attribute("aria-label").strip()

        if not label_org:
            continue

        # Select
        select_el = try_xp(Question, ".//select", False)
        if select_el:
            try:
                selected = Select(select_el).first_selected_option.text
                if selected and selected != "Select an option":
                    options = [o.text for o in Select(select_el).options]
                    save_learned_answer(label_org, "select", selected, str(options))
                    print_lg(f'Captured manual select "{label_org}": "{selected}"')
            except Exception:
                pass
            continue

        # Text input
        text_el = try_xp(Question, ".//input[@type='text']", False)
        if text_el:
            val = text_el.get_attribute("value")
            if val and val.strip():
                save_learned_answer(label_org, "text", val.strip())
                print_lg(f'Captured manual text "{label_org}": "{val.strip()}"')
            continue

        # Textarea
        textarea_el = try_xp(Question, ".//textarea", False)
        if textarea_el:
            val = textarea_el.get_attribute("value")
            if val and val.strip():
                save_learned_answer(label_org, "textarea", val.strip())
                print_lg(f'Captured manual textarea "{label_org}": "{val.strip()}"')
            continue

        # Radio / checkbox groups — find selected ones
        all_checkboxes = Question.find_elements(By.XPATH, ".//input[@type='checkbox']")
        all_radios = Question.find_elements(By.XPATH, ".//input[@type='radio']")

        if all_radios:
            for radio in all_radios:
                if radio.is_selected():
                    radio_id = radio.get_attribute("id")
                    radio_label_el = try_xp(Question, f".//label[@for='{radio_id}']", False)
                    radio_label = radio_label_el.text.strip() if radio_label_el else ""
                    if radio_label:
                        # Find all radio labels for options context
                        all_radio_labels = []
                        for r in all_radios:
                            rid = r.get_attribute("id")
                            rlbl = try_xp(Question, f".//label[@for='{rid}']", False)
                            if rlbl:
                                all_radio_labels.append(rlbl.text.strip())
                        save_learned_answer(label_org, "radio", radio_label, str(all_radio_labels))
                        print_lg(f'Captured manual radio "{label_org}": "{radio_label}"')
            continue

        if all_checkboxes:
            selected_labels = []
            all_cb_labels = []
            for cb in all_checkboxes:
                cb_id = cb.get_attribute("id")
                cb_label_el = try_xp(Question, f".//label[@for='{cb_id}']", False)
                cb_label = cb_label_el.text.strip() if cb_label_el else ""
                if cb_label:
                    all_cb_labels.append(cb_label)
                    if cb.is_selected():
                        selected_labels.append(cb_label)
            if selected_labels:
                save_learned_answer(label_org, "checkbox", ", ".join(selected_labels), str(all_cb_labels))
                print_lg(f'Captured manual checkbox "{label_org}": "{selected_labels}"')


def _retry_ai_answer(client, label: str, options, qtype: str, description: str, userProfile: dict, attempts: int = 2) -> str | None:
    ''' Call ai_answer_question with retries on failure '''
    for i in range(attempts):
        ai_answer = ai_answer_question(client, label, options, qtype, job_description=description, user_profile=userProfile)
        if ai_answer:
            return ai_answer
        if i < attempts - 1:
            print_lg(f'AI answer failed for "{label}" — retrying ({i + 2}/{attempts})...')
            buffer(2)
    return None


# Function to answer the questions for Easy Apply
def answer_questions(modal: WebElement, questions_list: set, work_location: str, description: str = "Unknown", userProfile: dict = None) -> set:
    # Get all questions from the page
    learned_answers = load_learned_answers()

    all_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    all_questions = all_questions + all_list_questions + all_single_line_questions

    for Question in all_questions:
        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            label_org = "Unknown"
            try:
                label = Question.find_element(By.TAG_NAME, "label")
                label_org = label.find_element(By.TAG_NAME, "span").text
            except Exception:
                pass  # Non-critical: select may not have a label/span structure
            answer = 'Yes'
            label = label_org.lower()
            select = Select(select)
            selected_option = select.first_selected_option.text
            optionsText = []
            options = '"List of phone country codes"'
            if label != "phone country code":
                optionsText = [option.text for option in select.options]
                options = "".join([f' "{option}",' for option in optionsText])
            prev_answer = selected_option
            if overwrite_previous_answers or selected_option == "Select an option":
                if 'email' in label or 'phone' in label: answer = prev_answer
                elif 'gender' in label or 'sex' in label: answer = gender
                elif 'disability' in label: answer = disability_status
                elif ('proficiency' in label or 'english' in label or 'anglais' in label or 'ingles' in label or 'inglés' in label
                      or 'language' in label or 'idioma' in label or 'langue' in label or 'sprache' in label
                      or 'nivel' in label or 'niveau' in label):
                    # Multi-language language proficiency detection
                    answer = 'Professional'
                    prof_levels = [
                        'Native or bilingual', 'Native Speaker', 'Native', 'Nativo', 'Bilingüe', 'Bilingue',
                        'Fluent', 'Fluido', 'Fluente', 'C2', 'C1', 'Professional', 'Profesional',
                        'Advanced', 'Avanzado', 'Avancé', 'B2', 'Conversational', 'Conversacional', 'B1',
                        'Intermediate', 'Intermedio', 'Intermédiaire', 'A2', 'Basic', 'Básico', 'Basico', 'A1'
                    ]
                    for prof in prof_levels:
                        if any(prof.lower() in opt.lower() for opt in optionsText):
                            answer = prof
                            break
                else: answer = answer_common_questions(label,answer)
                try: select.select_by_visible_text(answer)
                except NoSuchElementException as e:
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    foundOption = False
                    for phrase in possible_answer_phrases:
                        for option in optionsText:
                            if phrase in option:
                                select.select_by_visible_text(option)
                                answer = f'Decline ({option})' if len(possible_answer_phrases) > 1 else option
                                foundOption = True
                                break
                        if foundOption: break
                    if not foundOption:
                        learned_answer = find_learned_answer(label_org, "select")
                        if learned_answer:
                            try:
                                select.select_by_visible_text(learned_answer)
                                answer = learned_answer
                                foundOption = True
                                print_lg(f'Used learned answer for select "{label_org}": "{learned_answer}"')
                            except NoSuchElementException:
                                print_lg(f'Learned answer "{learned_answer}" not found in options for "{label_org}"')
                        if not foundOption and use_AI and aiClient:
                            ai_answer = _retry_ai_answer(aiClient, label_org, optionsText, 'single_select', description, userProfile)
                            if ai_answer:
                                try:
                                    select.select_by_visible_text(ai_answer)
                                    answer = ai_answer
                                    foundOption = True
                                    save_learned_answer(label_org, "select", ai_answer, str(optionsText))
                                    print_lg(f'Used AI answer for select "{label_org}": "{ai_answer}"')
                                except NoSuchElementException:
                                    print_lg(f'AI answer "{ai_answer}" not found in options for "{label_org}"')
                                    # Fuzzy fallback: try substring match first (fast), then similarity (handles translations)
                                    best_match = None
                                    best_score = 0.0
                                    for i, opt in enumerate(optionsText):
                                        # Substring match (e.g. "Fluent" in "Fluido")
                                        if ai_answer.lower() in opt.lower() or opt.lower() in ai_answer.lower():
                                            best_match = i
                                            break
                                        # Similarity fallback (e.g. "Advanced" vs "Avanzado")
                                        score = _similarity(ai_answer.lower(), opt.lower())
                                        if score > best_score:
                                            best_score = score
                                            best_match = i
                                    if best_match is not None and (best_score >= 0.5 or best_match == i):
                                        opt = optionsText[best_match]
                                        select.select_by_index(best_match + 1)  # +1 to skip placeholder
                                        answer = opt
                                        foundOption = True
                                        save_learned_answer(label_org, "select", opt, str(optionsText))
                                        print_lg(f'Used AI answer (fuzzy) for select "{label_org}": "{opt}" (AI said "{ai_answer}")')
                        elif not foundOption:
                            # Log WHY AI wasn't called so it's diagnosable
                            if not use_AI:
                                print_lg(f'AI NOT called for select "{label_org}" — use_AI is False in config/secrets.py')
                            elif not aiClient:
                                print_lg(f'AI NOT called for select "{label_org}" — AI client is None (API connection may have failed at startup)')
                        if not foundOption:
                            print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                            select.select_by_index(randint(1, len(select.options)-1))
                            answer = select.first_selected_option.text
                            randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
            questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
            continue
        
        # Check if it's a radio Question
        radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
        if radio:
            prev_answer = None
            label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
            try: label = find_by_class(label, "visually-hidden", 2.0)
            except Exception:
                pass  # Non-critical: visually-hidden class may not exist
            label_org = label.text if label else "Unknown"
            answer = 'Yes'
            label = label_org.lower()

            label_org += ' [ '
            options = radio.find_elements(By.TAG_NAME, 'input')
            options_labels = []
            
            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append( f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>' ) # Saving option as "label <value>"
                if option.is_selected(): prev_answer = options_labels[-1]
                label_org += f' {options_labels[-1]},'

            if overwrite_previous_answers or prev_answer is None:
                if 'citizenship' in label or 'employment eligibility' in label: answer = us_citizenship
                elif 'veteran' in label or 'protected' in label: answer = veteran_status
                elif 'disability' in label or 'handicapped' in label: 
                    answer = disability_status
                else: answer = answer_common_questions(label,answer)
                foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                if foundOption:
                    actions.move_to_element(foundOption).click().perform()
                else:
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                break
                        if foundOption: break
                    if not foundOption:
                        learned_answer = find_learned_answer(label_org, "radio")
                        if learned_answer:
                            learned_radio = try_xp(radio, f".//label[normalize-space()='{learned_answer}']", False)
                            if learned_radio:
                                actions.move_to_element(learned_radio).click().perform()
                                answer = learned_answer
                                foundOption = True
                                print_lg(f'Used learned answer for radio "{label_org}": "{learned_answer}"')
                            else:
                                possibilities = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if learned_answer == 'Decline' else [learned_answer]
                                for phrase in possibilities:
                                    for i, opt_label in enumerate(options_labels):
                                        if phrase in opt_label:
                                            actions.move_to_element(options[i]).click().perform()
                                            answer = opt_label
                                            foundOption = True
                                            print_lg(f'Used learned answer for radio "{label_org}": "{opt_label}"')
                                            break
                                    if foundOption: break
                    if not foundOption and use_AI and aiClient:
                        option_labels_clean = [ol[:ol.rfind('<')] if '<' in ol else ol for ol in options_labels]
                        ai_answer = _retry_ai_answer(aiClient, label_org, option_labels_clean, 'single_select', description, userProfile)
                        if ai_answer:
                            ai_radio = try_xp(radio, f".//label[normalize-space()='{ai_answer}']", False)
                            if ai_radio:
                                actions.move_to_element(ai_radio).click().perform()
                                answer = ai_answer
                                foundOption = True
                                save_learned_answer(label_org, "radio", ai_answer, str(options_labels))
                                print_lg(f'Used AI answer for radio "{label_org}": "{ai_answer}"')
                            else:
                                # Fuzzy fallback: substring first, then similarity (handles translations)
                                best_match = None
                                best_score = 0.0
                                for i, opt_label in enumerate(options_labels):
                                    clean_label = option_labels_clean[i] if i < len(option_labels_clean) else opt_label
                                    if ai_answer.lower() in clean_label.lower() or clean_label.lower() in ai_answer.lower():
                                        best_match = i
                                        break
                                    score = _similarity(ai_answer.lower(), clean_label.lower())
                                    if score > best_score:
                                        best_score = score
                                        best_match = i
                                if best_match is not None and (best_score >= 0.5 or ai_answer.lower() in options_labels[best_match].lower()):
                                    actions.move_to_element(options[best_match]).click().perform()
                                    answer = options_labels[best_match]
                                    foundOption = True
                                    save_learned_answer(label_org, "radio", answer, str(options_labels))
                                    print_lg(f'Used AI answer (fuzzy) for radio "{label_org}": "{answer}" (AI said "{ai_answer}")')
                    elif not foundOption:
                        # Log WHY AI wasn't called
                        if not use_AI:
                            print_lg(f'AI NOT called for radio "{label_org}" — use_AI is False in config/secrets.py')
                        elif not aiClient:
                            print_lg(f'AI NOT called for radio "{label_org}" — AI client is None (API connection may have failed at startup)')
                    if not foundOption:
                        randomly_answered_questions.add((f'{label_org} ]',"radio"))
                        actions.move_to_element(ele).click().perform()
            else: answer = prev_answer
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question
        text = try_xp(Question, ".//input[@type='text']", False)
        if text: 
            do_actions = False
            label = try_xp(Question, ".//label[@for]", False)
            try: label = label.find_element(By.CLASS_NAME,'visually-hidden')
            except Exception:
                pass  # Non-critical: visually-hidden class may not exist on this text input
            label_org = label.text if label else "Unknown"
            answer = ""
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'experience' in label or 'years' in label: answer = ""  # Defer to AI — config value used as fallback below
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label: answer = street
                elif 'city' in label or 'location' in label or 'address' in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif 'signature' in label: answer = full_name # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif 'name' in label:
                    if 'full' in label: answer = full_name
                    elif 'first' in label and 'last' not in label: answer = first_name
                    elif 'middle' in label and 'last' not in label: answer = middle_name
                    elif 'last' in label and 'first' not in label: answer = last_name
                    elif 'employer' in label: answer = recent_employer
                    else: answer = full_name
                elif 'notice' in label:
                    if 'month' in label:
                        answer = notice_period_months
                    elif 'week' in label:
                        answer = notice_period_weeks
                    else: answer = notice_period
                elif 'salary' in label or 'salar' in label or 'compensation' in label or 'ctc' in label or 'pay' in label or 'remuneration' in label or 'wage' in label:
                    if 'current' in label or 'present' in label:
                        if 'month' in label:
                            answer = current_ctc_monthly
                        elif 'lakh' in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        if 'month' in label:
                            answer = desired_salary_monthly
                        elif 'lakh' in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                elif 'linkedin' in label: answer = linkedIn
                elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: answer = website
                elif 'scale of 1-10' in label: answer = confidence_level
                elif 'headline' in label: answer = linkedin_headline
                elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): answer = "LinkedIn"
                elif 'state' in label or 'province' in label: answer = state
                elif 'zip' in label or 'postal' in label or 'code' in label: answer = zipcode
                elif 'country' in label: answer = country
                elif 'english' in label or 'language' in label or 'proficiency' in label:
                    lang = "English"
                    for l in ["English", "Spanish", "French"]:
                        if l.lower() in label:
                            lang = l
                            break
                    lang_lower = lang.lower()
                    lang_data = (userProfile or {}).get('languages') or []
                    level = "Fluent"
                    for entry in lang_data:
                        if isinstance(entry, dict) and lang_lower in entry.get("language", "").lower():
                            level = entry.get("proficiency", entry.get("level", "Fluent"))
                            break
                    answer = level
                else: answer = answer_common_questions(label,answer)
                if answer == "":
                    learned_answer = find_learned_answer(label_org, "text")
                    if learned_answer:
                        answer = learned_answer
                        print_lg(f'Used learned answer for text "{label_org}": "{learned_answer}"')
                    elif use_AI and aiClient:
                        ai_answer = _retry_ai_answer(aiClient, label_org, None, 'text', description, userProfile)
                        if ai_answer:
                            answer = ai_answer
                            save_learned_answer(label_org, "text", ai_answer)
                            print_lg(f'Used AI answer for text "{label_org}": "{ai_answer}"')
                    else:
                        # Log WHY AI wasn't called for text questions
                        if answer == "":
                            if not use_AI:
                                print_lg(f'AI NOT called for text "{label_org}" — use_AI is False in config/secrets.py')
                            elif not aiClient:
                                print_lg(f'AI NOT called for text "{label_org}" — AI client is None (API connection may have failed at startup)')
                    if answer == "":
                        randomly_answered_questions.add((label_org, "text"))
                        answer = years_of_experience
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label = try_xp(Question, ".//label[@for]", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'summary' in label: answer = linkedin_summary
                elif 'cover' in label:
                    if use_AI and aiClient:
                        ai_cover = ai_generate_coverletter(aiClient, "", "", {}, userProfile)
                        answer = ai_cover if ai_cover else cover_letter
                    else:
                        answer = cover_letter
                text_area.clear()
                text_area.send_keys(answer)
                if answer == "":
                    learned_answer = find_learned_answer(label_org, "textarea")
                    if learned_answer:
                        answer = learned_answer
                        text_area.clear()
                        text_area.send_keys(answer)
                        print_lg(f'Used learned answer for textarea "{label_org}": "{learned_answer}"')
                    elif use_AI and aiClient:
                        ai_answer = _retry_ai_answer(aiClient, label_org, None, 'textarea', description, userProfile)
                        if ai_answer:
                            answer = ai_answer
                            text_area.clear()
                            text_area.send_keys(answer)
                            save_learned_answer(label_org, "textarea", ai_answer)
                            print_lg(f'Used AI answer for textarea "{label_org}": "{ai_answer}"')
                    else:
                        # Log WHY AI wasn't called for textarea questions
                        if answer == "":
                            if not use_AI:
                                print_lg(f'AI NOT called for textarea "{label_org}" — use_AI is False in config/secrets.py')
                            elif not aiClient:
                                print_lg(f'AI NOT called for textarea "{label_org}" — AI client is None (API connection may have failed at startup)')
                            print_lg(f'Used AI answer for textarea "{label_org}": "{ai_answer}"')
                if answer == "":
                    randomly_answered_questions.add((label_org, "textarea"))
            questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
            continue

        # Check if it's a checkbox question
        all_checkboxes = Question.find_elements(By.XPATH, ".//input[@type='checkbox']")
        if all_checkboxes:
            checkbox = all_checkboxes[0]
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(Question, ".//label[@for]", False)
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer

            if len(all_checkboxes) > 1:
                # Multiple checkboxes — "select all that apply" pattern
                checkbox_labels = []
                for cb in all_checkboxes:
                    cb_id = cb.get_attribute("id")
                    cb_label_el = try_xp(Question, f".//label[@for='{cb_id}']", False)
                    cb_label = cb_label_el.text if cb_label_el else "Unknown"
                    checkbox_labels.append(cb_label)

                if use_AI and aiClient:
                    ai_answer = _retry_ai_answer(aiClient, label_org, checkbox_labels, 'multiple_select', description, userProfile)
                    if ai_answer:
                        for cb in all_checkboxes:
                            cb_id = cb.get_attribute("id")
                            cb_label_el = try_xp(Question, f".//label[@for='{cb_id}']", False)
                            cb_label = cb_label_el.text if cb_label_el else ""
                            if ai_answer.lower() in cb_label.lower() and not cb.is_selected():
                                try:
                                    actions.move_to_element(cb).click().perform()
                                    print_lg(f'AI selected checkbox: "{cb_label}"')
                                except Exception as e:
                                    print_lg(f"Checkbox click failed for {cb_label}!", e)
                        checked = True
                        answer = ai_answer
                        save_learned_answer(label_org, "checkbox", ai_answer, str(checkbox_labels))
                        print_lg(f'Used AI answer for checkbox "{label_org}": "{ai_answer}"')
                    else:
                        # Fallback: check all
                        for cb in all_checkboxes:
                            if not cb.is_selected():
                                try:
                                    actions.move_to_element(cb).click().perform()
                                except Exception as e:
                                    print_lg("Checkbox click failed!", e)
                        checked = True
                else:
                    # No AI: check all as safest default
                    for cb in all_checkboxes:
                        if not cb.is_selected():
                            try:
                                actions.move_to_element(cb).click().perform()
                            except Exception as e:
                                print_lg("Checkbox click failed!", e)
                    checked = True
            else:
                # Single checkbox — existing behavior
                if not prev_answer:
                    learned_answer = find_learned_answer(label_org, "checkbox")
                    if learned_answer and learned_answer.lower() in ["yes", "true", "checked", "1"]:
                        try:
                            actions.move_to_element(checkbox).click().perform()
                            checked = True
                            save_learned_answer(label_org, "checkbox", "yes", str([answer]))
                            print_lg(f'Used learned answer for checkbox "{label_org}": checked')
                        except Exception as e:
                            print_lg("Checkbox click failed!", e)
                    elif not learned_answer:
                        try:
                            actions.move_to_element(checkbox).click().perform()
                            checked = True
                            save_learned_answer(label_org, "checkbox", "yes", str([answer]))
                        except Exception as e:
                            print_lg("Checkbox click failed!", e)
            questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
            continue


    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list




def external_apply(page_buttons, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Function to open new tab and save external job application links
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        try:
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text: dailyEasyApplyLimitReached = True
        except Exception:
            pass  # Non-critical: limit message element may not be present
        print_lg("Easy apply failed I guess!")
        if page_buttons is not None: return True, application_link, tabs_count
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]"))).click() # './/button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'
        wait_span_click(driver, "Continue", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count



def follow_company(modal: WebDriver = driver) -> None:
    '''
    Function to follow or un-follow easy applied companies based om `follow_companies`
    '''
    try:
        follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
        if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
    


#< Failed attempts logging
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':job_id, 'Job Link':job_link, 'Resume Tried':resume, 'Date listed':date_listed, 'Date Tried':datetime.now(), 'Assumed Reason':error, 'Stack Trace':exception, 'External Job link':application_link, 'Screenshot Name':screenshot_name})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':job_id, 'Title':title, 'Company':company, 'Work Location':work_location, 'Work Style':work_style, 
                            'About Job':description, 'Experience required': experience_required, 'Skills required':skills, 
                                'HR Name':hr_name, 'HR Link':hr_link, 'Resume':resume, 'Re-posted':reposted, 
                                'Date Posted':date_listed, 'Date Applied':date_applied, 'Job Link':job_link, 
                                'External Job link':application_link, 'Questions Found':questions_list, 'Connect Request':connect_request})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")



# Function to discard the job application
def discard_job() -> None:
    actions.send_keys(Keys.ESCAPE).perform()
    wait_span_click(driver, 'Discard', 2)


def check_verification_page() -> bool:
    '''
    Checks if LinkedIn is showing a security verification / CAPTCHA page.
    Returns True if verification is detected.
    '''
    try:
        page_source = driver.page_source.lower()
        verification_phrases = [
            "verify you're a human",
            "security verification",
            "let's do a quick security check",
            "unusual activity",
            "verify your identity"
        ]
        for phrase in verification_phrases:
            if phrase in page_source:
                # Confirm the phrase is actually visible, not just buried in a script tag
                try:
                    visible_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{phrase}')]")
                    if not visible_elements:
                        continue
                except Exception:
                    pass
                print_lg(f"SECURITY VERIFICATION DETECTED: Found '{phrase}' on page!")
                screenshot_path = logs_folder_path + "/screenshots/verification_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
                try:
                    driver.save_screenshot(screenshot_path)
                    print_lg(f"Saved verification screenshot to: {screenshot_path}")
                except Exception:
                    pass
                return True
    except Exception as e:
        print_lg(f"Error checking for verification page: {e}")
    return False


# Function to apply to jobs
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume
    current_city = current_city.strip()

    if randomize_search_order:  shuffle(search_terms)
    for searchTerm in search_terms:
        driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
        print_lg("\n________________________________________________________________________________________________________________________\n")
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')

        apply_filters()

        current_count = 0
        try:
            while current_count < switch_number:
                # Wait until job listings are loaded
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))

                page_buttons, current_page = get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")  

            
                for job in job_listings:
                    if keep_screen_awake: pyautogui.press('shiftright')
                    if current_count >= switch_number: break
                    if easy_applied_count >= max_daily_applications:
                        print_lg(f"\n###############  Daily application limit reached ({max_daily_applications})!  ###############\n")
                        dailyEasyApplyLimitReached = True
                        return
                    print_lg("\n-@-\n")

                    if check_verification_page():
                        screenshot_path = logs_folder_path + "/screenshots/verification_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
                        try:
                            driver.save_screenshot(screenshot_path)
                        except Exception:
                            pass
                        pyautogui.alert("LinkedIn is showing a security verification page! Please solve the CAPTCHA/verification manually, then click OK to continue.", "Verification Required", "OK")
                        if check_verification_page():
                            print_lg("Verification still detected after manual intervention. Pausing 5 minutes...")
                            sleep(300)

                    job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                    
                    if skip: continue
                    # Redundant fail safe check for applied jobs!
                    try:
                        if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
                            continue
                    except Exception as e:
                        print_lg(f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}')

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link = "Unknown"
                    hr_name = "Unknown"
                    connect_request = "In Development" # Still in development
                    date_listed = "Unknown"
                    skills = "Needs an AI" # Still in development
                    resume = "Pending"
                    reposted = False
                    questions_list = None
                    screenshot_name = "Not Available"

                    try:
                        rejected_jobs, blacklisted_companies, jobs_top_card = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                    except ValueError as e:
                        print_lg(e, 'Skipping this job!\n')
                        failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                        skip_count += 1
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!")
                        # print_lg(e)



                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                        hr_link = hr_info_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text
                    except Exception as e:
                        print_lg(f'HR info was not given for "{title}" with Job ID: {job_id}!')
                        # print_lg(e)


                    # Calculation of date posted
                    try:
                        time_posted_text = jobs_top_card.find_element(By.XPATH, './/span[contains(normalize-space(), " ago")]').text
                        print("Time Posted: " + time_posted_text)
                        if time_posted_text.__contains__("Reposted"):
                            reposted = True
                            time_posted_text = time_posted_text.replace("Reposted", "")
                        date_listed = calculate_date_posted(time_posted_text)
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!",e)


                    description, experience_required, skip, reason, message = get_job_description()
                    if skip:
                        print_lg(message)
                        failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                        rejected_jobs.add(job_id)
                        skip_count += 1
                        continue

                    
                    if use_AI and description != "Unknown":
                        skills = ai_extract_skills(aiClient, description)

                    uploaded = False
                    # Case 1: Easy Apply Button
                    if try_xp(driver, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]"):
                        try: 
                            try:
                                errored = ""
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                wait_span_click(modal, "Next", 1)
                                resume = "Previous resume"
                                next_button = True
                                questions_list = set()
                                next_counter = 0
                                paused_count = 0  # Track how many times we've paused for manual help
                                while next_button:
                                    next_counter += 1
                                    if next_counter >= 15:
                                        if pause_at_failed_question and paused_count < 2:
                                            paused_count += 1
                                            screenshot(driver, job_id, f"Needed manual intervention (attempt {paused_count}/2)")
                                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                                            capture_manual_answers(modal)
                                            next_counter = 1
                                            continue
                                        if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                        screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        errored = "stuck"
                                        raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                                    questions_list = answer_questions(modal, questions_list, work_location, description, userProfile)
                                    if useNewResume and not uploaded: uploaded, resume = upload_resume(modal, default_resume_path)
                                    try: next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Review"]') 
                                    except NoSuchElementException:  next_button = modal.find_element(By.XPATH, './/button[contains(span, "Next")]')
                                    try: next_button.click()
                                    except ElementClickInterceptedException: break    # Happens when it tries to click Next button in About Company photos section
                                    buffer(click_gap)

                            except NoSuchElementException: errored = "nose"
                            finally:
                                if questions_list and errored != "stuck": 
                                    print_lg("Answered the following questions...", questions_list)
                                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                wait_span_click(driver, "Review", 1, scrollTop=True)
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                    if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                    pause_before_submit = False if "Disable Pause" == decision else True
                                    capture_manual_answers(modal)
                                    # try_xp(modal, ".//span[normalize-space(.)='Review']")
                                follow_company(modal)
                                if wait_span_click(driver, "Submit application", 2, scrollTop=True): 
                                    date_applied = datetime.now()
                                    if not wait_span_click(driver, "Done", 2): actions.send_keys(Keys.ESCAPE).perform()
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                    date_applied = datetime.now()
                                    wait_span_click(driver, "Done", 2)
                                else:
                                    print_lg("Since, Submit Application failed, discarding the job application...")
                                    if errored == "nose": raise Exception("Failed to click Submit application 😑")


                        except Exception as e:
                            print_lg("Failed to Easy apply!")
                            # print_lg(e)
                            critical_error_log("Somewhere in Easy Apply process",e)
                            failed_job(job_id, job_link, resume, date_listed, "Problem in Easy Applying", e, application_link, screenshot_name)
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Case 2: Apply externally
                        skip, application_link, tabs_count = external_apply(page_buttons, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                        if dailyEasyApplyLimitReached:
                            print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                            return
                        if skip: continue

                    submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                    if uploaded:   useNewResume = False

                    print_lg(f'Successfully saved "{title} | {company}" job. Job ID: {job_id} info')
                    current_count += 1
                    if application_link == "Easy Applied": easy_applied_count += 1
                    else:   external_jobs_count += 1
                    applied_jobs.add(job_id)
                    buffer(min_job_gap)



                # Switching to next page
                if page_buttons is None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    # Re-fetch page buttons fresh to avoid stale element references
                    # after DOM changes from clicking through job listings
                    fresh_buttons, _ = get_page_info()
                    if fresh_buttons is None:
                        print_lg("Pagination disappeared, probably at the end page of results!")
                        break
                    next_page_btn = None
                    for btn in fresh_buttons:
                        label = btn.get_attribute("aria-label") or ""
                        if label == f"Page {current_page + 1}":
                            next_page_btn = btn
                            break
                    if next_page_btn is None:
                        print_lg(f"\n>-> Didn't find Page {current_page + 1}. Probably at the end page of results!\n")
                        break
                    scroll_to_view(driver, next_page_btn)
                    next_page_btn.click()
                    print_lg(f"\n>-> Now on Page {current_page + 1} \n")
                except (NoSuchElementException, StaleElementReferenceException):
                    print_lg(f"\n>-> Didn't find Page {current_page + 1}. Probably at the end page of results!\n")
                    break

        except Exception as e:
            print_lg("Failed to find Job listings!")
            critical_error_log("In Applier", e)
            print_lg(driver.page_source, pretty=True)
            # print_lg(e)

        
def ensure_ai_client() -> None:
    ''' Reconnects AI client if it was lost (e.g. transient API error on startup) '''
    global aiClient, userProfile
    if use_AI and not aiClient:
        print_lg("AI client is missing — attempting to reconnect...")
        aiClient = ai_create_openai_client()
        if aiClient:
            userProfile = get_user_profile(aiClient, ai_completion, default_resume_path)


def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    ensure_ai_client()
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'")
    apply_to_jobs(search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached:
        print_lg("Sleeping for 10 min...")
        sleep(300)
        print_lg("Few more min... Gonna start with in next 5 min...")
        sleep(300)
    buffer(3)
    return total_runs + 1



linkedIn_tab = False

def main() -> None:
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        total_runs = 1        
        validate_config()

        global driver, wait, actions
        driver, wait, actions = initialize_driver()

        if not os.path.exists(default_resume_path):
            pyautogui.alert(text='Your default resume "{}" is missing! Please update it\'s folder path "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!'.format(default_resume_path), title="Missing Resume", button="OK")
            useNewResume = False
        
        # Login to LinkedIn
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        
        linkedIn_tab = driver.current_window_handle

        ensure_ai_client()

        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                date_posted = date_options[date_options.index(date_posted)+1 if date_options.index(date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(date_posted)+1 >= len(date_options) else date_options.index(date_posted)+1]
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached:
                break
        

    except NoSuchWindowException:
        print_lg("Browser window was closed unexpectedly. Exiting.")
    except Exception as e:
        critical_error_log("In Applier Main", e)
        pyautogui.alert(e,alert_title)
    finally:
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))
        # quote = choice([
        #     "You're one step closer than before.",
        #     "All the best with your future interviews.",
        #     "Keep up with the progress. You got this.",
        #     "If you're tired, learn to take rest but never give up.",
        #     "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
        #     "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
        #     "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
        #     "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
        #     "Opportunities don't happen, you create them. - Chris Grosser",
        #     "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
        #     "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
        #     "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
        #     ])
        # msg = f"\n{quote}\n\n\nBest regards,\nTom"
        # pyautogui.alert(msg, "Exiting..")
        # print_lg(msg,"Closing the browser...")
        print_lg("Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            pyautogui.alert(msg,"Info")
            print_lg("\n"+msg)
        ai_close_openai_client(aiClient)
        try: driver.quit()
        except Exception as e: critical_error_log("When quitting...", e)


if __name__ == "__main__":
    main()
