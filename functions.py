import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import streamlit as st
from sqlalchemy import text
from pandas.core.methods.to_dict import to_dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

@st.cache_data(ttl=60)
def init_db():
    conn = st.connection('versions_db', type='sql')
    with conn.session as s:
        s.execute(text(
            'CREATE TABLE IF NOT EXISTS versions (id TEXT, platform TEXT, browser TEXT, channel TEXT, version TEXT, success_check TEXT, fail_check TEXT, error_message TEXT);'))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
            SELECT 'chrome_stable', 'browser_extension', 'chrome', 'stable', '', '0', '0', ''
            WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'chrome_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'edge_stable', 'browser_extension', 'edge', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'edge_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'firefox_stable', 'browser_extension', 'firefox', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'firefox_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'safari_stable', 'browser_extension', 'safari', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'safari_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opi_stable', 'mobile', 'opi', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opi_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opa_stable', 'mobile', 'opa', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opa_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opw_stable', 'desktop', 'opw', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opw_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opm_stable', 'desktop', 'opm', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opm_stable');"""
        ))
        s.commit()

# Set up our database connection
@st.cache_data(ttl=60)
def db_dict(platform):
    conn = st.connection('versions_db', type='sql', ttl=60)

    # Query the database, which returns a pandas dataframe, then convert it to a dict
    versions = conn.query(f'select * from versions WHERE platform = "{platform}"')
    versions_dict = to_dict(versions, orient='index')
    return versions_dict


@st.cache_data(ttl=60)
def should_we_scrape():
    conn = st.connection('versions_db', type='sql')
    versions = conn.query('select * from versions')
    versions_dict = to_dict(versions, orient='index')

    current_epoch = datetime.now().timestamp()

    for index, version in enumerate(versions_dict):
        success_next_check = float(versions_dict[index]['success_check']) + 3600
        fail_next_check = float(versions_dict[index]['fail_check']) + 3600
        # We only want to use the latest timestamp
        next_check = max(success_next_check, fail_next_check)
        if current_epoch > next_check:
            return True

    return False

def format_datetime(date_time):
    utc_time = datetime.fromtimestamp(float(date_time), timezone.utc)
    local_time = utc_time.astimezone()
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M')
    return formatted_time

def format_name(name):
    if len(name) > 3:
        formatted_name = name.capitalize()
    else:
        formatted_name = name.upper()
    return formatted_name

def edge_stable_api():
    url = 'https://microsoftedge.microsoft.com/addons/getproductdetailsbycrxid/dppgmdbiimibapkepcbdbmkaabgiofem?hl=en-US'
    success_time = False
    fail_time = False
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['version']
        success_time = datetime.now().timestamp()
    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = e
    conn = st.connection('versions_db', type='sql')
    if success_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :edge_version, success_check = :edge_success WHERE id = :edge_stable;"),
                {"edge_version": version, "edge_success": success_time, "edge_stable": "edge_stable"},)
            s.commit()
    elif fail_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :edge_fail, error_message = :edge_error WHERE id = :edge_stable;"),
                {"edge_fail": fail_time, "edge_error": error_msg, "edge_stable": "edge_stable"},)
            s.commit()
    return

def chrome_stable_scrape():
    url = 'https://chromewebstore.google.com/detail/1password-%E2%80%93-password-mana/aeblfdkhhhdcdjpifhhbdiojplfjncoa'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    version_element = soup.find(string="Version")
    if version_element:
        # The version number appears right *after* that text
        version_text = version_element.find_next().get_text(strip=True)
        conn = st.connection('versions_db', type='sql')
        if version_text:
            success_time = datetime.now().timestamp()
            with conn.session as s:
                s.execute(text(
                    "UPDATE versions SET version = :chrome_version, success_check = :chrome_success WHERE id = :chrome_stable;"),
                    {"chrome_version": version_text, "chrome_success": success_time, "chrome_stable": "chrome_stable"}, )
                s.commit()
        else:
            fail_time = datetime.now().timestamp()
            error_msg = "Scrape failed."
            with conn.session as s:
                s.execute(text(
                    "UPDATE versions SET fail_check = :chrome_fail, error_message = :chrome_error WHERE id = :chrome_stable;"),
                    {"chrome_fail": fail_time, "chrome_error": error_msg, "chrome_stable": "chrome_stable"}, )
                s.commit()
    return

def firefox_stable_scrape():
    url = 'https://addons.mozilla.org/api/v5/addons/addon/1password-x-password-manager/'
    success_time = False
    fail_time = False
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['current_version']['version']
        success_time = datetime.now().timestamp()
    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = e
    conn = st.connection('versions_db', type='sql')
    if success_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :firefox_version, success_check = :firefox_success WHERE id = :firefox_stable;"),
                {"firefox_version": version, "firefox_success": success_time,
                 "firefox_stable": "firefox_stable"}, )
            s.commit()
    elif fail_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :firefox_fail, error_message = :firefox_error WHERE id = :firefox_stable;"),
                {"firefox_fail": fail_time, "firefox_error": error_msg, "firefox_stable": "firefox_stable"}, )
            s.commit()
    return

def safari_stable_scrape():
    url = 'https://itunes.apple.com/lookup?id=1569813296'
    success_time = False
    fail_time = False
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['results'][0]['version']
        success_time = datetime.now().timestamp()
    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = e
    conn = st.connection('versions_db', type='sql')
    if success_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :safari_version, success_check = :safari_success WHERE id = :safari_stable;"),
                {"safari_version": version, "safari_success": success_time, "safari_stable": "safari_stable"}, )
            s.commit()
    elif fail_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :safari_fail, error_message = :safari_error WHERE id = :safari_stable;"),
                {"safari_fail": fail_time, "safari_error": error_msg, "safari_stable": "safari_stable"}, )
            s.commit()
    return

def opi_stable_scrape():
    url = 'https://itunes.apple.com/lookup?id=1511601750'
    success_time = False
    fail_time = False
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['results'][0]['version']
        success_time = datetime.now().timestamp()
    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = e
    conn = st.connection('versions_db', type='sql')
    if success_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :opi_version, success_check = :opi_success WHERE id = :opi_stable;"),
                {"opi_version": version, "opi_success": success_time, "opi_stable": "opi_stable"}, )
            s.commit()
    elif fail_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opi_fail, error_message = :opi_error WHERE id = :opi_stable;"),
                {"opi_fail": fail_time, "opi_error": error_msg, "opi_stable": "opi_stable"}, )
            s.commit()
    return

def opa_stable_scrape():
    url = "https://play.google.com/store/apps/details?id=com.onepassword.android"
    conn = st.connection("versions_db", type="sql")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                # Optional but often helpful:
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=60_000)

            # Wait for the page to be interactive enough that the About button exists
            about_btn = '[aria-label="See more information on About this app"]'
            page.wait_for_selector(about_btn, timeout=60_000)

            # Click "About this app" (your old JS click, but as a real click)
            page.click(about_btn)

            # Wait for the Version label to appear in the expanded content / dialog
            page.wait_for_selector("text=Version", timeout=60_000)

            # Pull the fully-rendered HTML after the click
            html = page.content()

            context.close()
            browser.close()

        # Parse with BeautifulSoup (same as before)
        soup = BeautifulSoup(html, "html.parser")

        version_element = soup.find(string="Version")
        version_text = None
        if version_element:
            # This mirrors your existing logic; depending on Play Store markup,
            # you may need to adjust (see note below).
            nxt = version_element.find_next()
            if nxt:
                version_text = nxt.get_text(strip=True) or None

        if version_text:
            success_time = datetime.now().timestamp()
            with conn.session as s:
                s.execute(
                    text(
                        "UPDATE versions "
                        "SET version = :opa_version, success_check = :opa_success "
                        "WHERE id = :opa_stable;"
                    ),
                    {
                        "opa_version": version_text,
                        "opa_success": success_time,
                        "opa_stable": "opa_stable",
                    },
                )
                s.commit()
        else:
            fail_time = datetime.now().timestamp()
            error_msg = "Scrape failed: could not find Version text/value."
            with conn.session as s:
                s.execute(
                    text(
                        "UPDATE versions "
                        "SET fail_check = :opa_fail, error_message = :opa_error "
                        "WHERE id = :opa_stable;"
                    ),
                    {
                        "opa_fail": fail_time,
                        "opa_error": error_msg,
                        "opa_stable": "opa_stable",
                    },
                )
                s.commit()

    except PlaywrightTimeoutError as e:
        fail_time = datetime.now().timestamp()
        error_msg = f"Scrape failed: Playwright timeout. {e!s}"
        with conn.session as s:
            s.execute(
                text(
                    "UPDATE versions "
                    "SET fail_check = :opa_fail, error_message = :opa_error "
                    "WHERE id = :opa_stable;"
                ),
                {
                    "opa_fail": fail_time,
                    "opa_error": error_msg,
                    "opa_stable": "opa_stable",
                },
            )
            s.commit()

    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = f"Scrape failed: {type(e).__name__}: {e}"
        with conn.session as s:
            s.execute(
                text(
                    "UPDATE versions "
                    "SET fail_check = :opa_fail, error_message = :opa_error "
                    "WHERE id = :opa_stable;"
                ),
                {
                    "opa_fail": fail_time,
                    "opa_error": error_msg,
                    "opa_stable": "opa_stable",
                },
            )
            s.commit()

    return

def opw_stable_scrape():
    url = 'https://app-updates.agilebits.com/check/3/26.2.0/arm64/OPW8/en/8/ab/production/unkown'
    success_time = False
    fail_time = False
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['version']
        success_time = datetime.now().timestamp()
    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = e
    conn = st.connection('versions_db', type='sql')
    if success_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :opw_version, success_check = :opw_success WHERE id = :opw_stable;"),
                {"opw_version": version, "opw_success": success_time, "opw_stable": "opw_stable"}, )
            s.commit()
    elif fail_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opw_fail, error_message = :opw_error WHERE id = :opw_stable;"),
                {"opw_fail": fail_time, "opw_error": error_msg, "opw_stable": "opw_stable"}, )
            s.commit()

    return

def opm_stable_scrape():
    url = 'https://app-updates.agilebits.com/check/3/26.2.0/arm64/OPM8/en/8/ab/production/unkown'
    success_time = False
    fail_time = False
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['version']
        success_time = datetime.now().timestamp()
    except Exception as e:
        fail_time = datetime.now().timestamp()
        error_msg = e
    conn = st.connection('versions_db', type='sql')
    if success_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :opm_version, success_check = :opm_success WHERE id = :opm_stable;"),
                {"opm_version": version, "opm_success": success_time, "opm_stable": "opm_stable"}, )
            s.commit()
    elif fail_time:
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opm_fail, error_message = :opm_error WHERE id = :opm_stable;"),
                {"opm_fail": fail_time, "opm_error": error_msg, "opm_stable": "opm_stable"}, )
            s.commit()

    return


# chrome beta: https://chromewebstore.google.com/detail/1password-beta-%E2%80%93-password/khgocmkkpikpnmmkgmdnfckapcdkgfaf
# chrome nightly: https://chromewebstore.google.com/detail/1password-nightly-%E2%80%93-passw/gejiddohjgogedgjnonbofjigllpkmbf
# firefox stable: https://addons.mozilla.org/en-US/firefox/addon/1password-x-password-manager/
# firefox beta: https://c.1password.com/dist/1P/b5x/firefox/beta/updates.json
# firefox nightly: https://c.1password.com/dist/1P/b5x/firefox/nightly/updates.json
# safari: https://itunes.apple.com/lookup?bundleId=%scom.1password.safari
# opi: https://itunes.apple.com/lookup?bundleId=%s com.1password.1password
# opa: https://play.google.com/store/apps/details?id=com.onepassword.android
# opw: