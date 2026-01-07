import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import streamlit as st
from sqlalchemy import text
from pandas.core.methods.to_dict import to_dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import gzip
import io
from debian import debian_support
from rpm_vercmp import vercmp
import xml.etree.ElementTree as ET

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
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opl_deb_stable', 'desktop', 'opl_deb', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opl_deb_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, platform, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opl_rpm_stable', 'desktop', 'opl_rpm', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opl_rpm_stable');"""
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
    match name:
        case 'chrome': return 'Chrome'
        case 'edge': return 'Edge'
        case 'firefox': return 'Firefox'
        case 'safari': return 'Safari'
        case 'opi': return 'iOS'
        case 'opa': return 'Android'
        case 'opw': return 'Windows'
        case 'opm': return 'macOS'
        case 'opl_deb': return 'Linux (deb)'
        case 'opl_rpm': return 'Linux (rpm)'
        case _: return name

def edge_stable_call():
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

def firefox_stable_call():
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

def safari_stable_call():
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

def opi_stable_call():
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

def opw_stable_call():
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

def opm_stable_call():
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

def opl_deb_stable_call(timeout: float = 10.0) -> str:
    url = "https://downloads.1password.com/linux/debian/amd64/dists/stable/main/binary-amd64/Packages.gz"

    request = requests.get(url, stream=True, timeout=timeout)
    request.raise_for_status()

    # Stream gzip -> text lines
    gz = gzip.GzipFile(fileobj=request.raw)
    gz_text = io.TextIOWrapper(gz, encoding="utf-8", errors="replace")

    version = None
    in_target = False

    for line in gz_text:
        line = line.rstrip("\n")

        # Blank line = end of stanza
        if not line:
            in_target = False
            continue

        if line.startswith("Package:"):
            in_target = (line.split(":", 1)[1].strip() == "1password")
            continue

        if in_target and line.startswith("Version:"):
            v = line.split(":", 1)[1].strip()
            if version is None or debian_support.Version(v) > debian_support.Version(version):
                version = v

    conn = st.connection('versions_db', type='sql')
    if version:
        success_time = datetime.now().timestamp()
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :opl_version, success_check = :opl_success WHERE id = :opl_deb_stable;"),
                {"opl_version": version, "opl_success": success_time, "opl_deb_stable": "opl_deb_stable"}, )
            s.commit()
    elif version is None:
        fail_time = datetime.now().timestamp()
        error_msg = "Package '1password' not found in Packages.gz"
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opl_fail, error_message = :opl_error WHERE id = :opl_deb_stable;"),
                {"opl_fail": fail_time, "opl_error": error_msg, "opl_deb_stable": "opl_deb_stable"}, )
            s.commit()
    else:
        fail_time = datetime.now().timestamp()
        error_msg = "Unknown error occurred"
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opl_fail, error_message = :opl_error WHERE id = :opl_deb_stable;"),
                {"opl_fail": fail_time, "opl_error": error_msg, "opl_deb_stable": "opl_deb_stable"}, )
            s.commit()

    return

def opl_rpm_stable_call(
        basearch: str = "x86_64",
        timeout: float = 10.0,
) -> str:

    baseurl = "https://downloads.1password.com/linux/rpm/stable"

    def strip_ns(tag: str) -> str:
        return tag.rsplit("}", 1)[-1] if "}" in tag else tag

    def compare_evr(a, b) -> int:
        ea, va, ra = a
        eb, vb, rb = b

        ea = int(ea or 0)
        eb = int(eb or 0)
        if ea != eb:
            return -1 if ea < eb else 1

        c = vercmp(va or "", vb or "")
        if c != 0:
            return c

        return vercmp(ra or "", rb or "")

    # repomd.xml
    repomd_url = f"{baseurl}/{basearch}/repodata/repomd.xml"
    r = requests.get(repomd_url, timeout=timeout)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    primary_href = None
    for data in root.iter():
        if strip_ns(data.tag) == "data" and data.attrib.get("type") == "primary":
            for child in data.iter():
                if strip_ns(child.tag) == "location":
                    primary_href = child.attrib.get("href")
                    break
        if primary_href:
            break

    if not primary_href:
        raise LookupError("primary metadata not found")

    # primary.xml.gz
    primary_url = f"{baseurl}/{basearch}/{primary_href}"
    r = requests.get(primary_url, timeout=timeout)
    r.raise_for_status()

    gz = gzip.GzipFile(fileobj=io.BytesIO(r.content))
    xml_buf = io.BytesIO(gz.read())

    best_evr = None

    for _, elem in ET.iterparse(xml_buf, events=("end",)):
        if strip_ns(elem.tag) != "package":
            continue

        name = None
        evr = None

        for child in elem:
            tag = strip_ns(child.tag)
            if tag == "name":
                name = (child.text or "").strip()
            elif tag == "version":
                evr = (
                    child.attrib.get("epoch", "0"),
                    child.attrib.get("ver", ""),
                    child.attrib.get("rel", ""),
                )

        if name == "1password" and evr:
            if best_evr is None or compare_evr(evr, best_evr) > 0:
                best_evr = evr

        elem.clear()

    if best_evr is None:
        raise LookupError("Package '1password' not found")

    conn = st.connection('versions_db', type='sql')
    if best_evr:
        success_time = datetime.now().timestamp()
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET version = :opl_version, success_check = :opl_success WHERE id = :opl_rpm_stable;"),
                {"opl_version": best_evr[1], "opl_success": success_time, "opl_rpm_stable": "opl_rpm_stable"}, )
            s.commit()
    elif best_evr is None:
        fail_time = datetime.now().timestamp()
        error_msg = "Package '1password' not found"
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opl_fail, error_message = :opl_error WHERE id = :opl_rpm_stable;"),
                {"opl_fail": fail_time, "opl_error": error_msg, "opl_rpm_stable": "opl_rpm_stable"}, )
            s.commit()
    else:
        fail_time = datetime.now().timestamp()
        error_msg = "Unknown error occurred"
        with conn.session as s:
            s.execute(text(
                "UPDATE versions SET fail_check = :opl_fail, error_message = :opl_error WHERE id = :opl_rpm_stable;"),
                {"opl_fail": fail_time, "opl_error": error_msg, "opl_rpm_stable": "opl_rpm_stable"}, )
            s.commit()

    return
