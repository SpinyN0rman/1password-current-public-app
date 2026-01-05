import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import streamlit as st
from sqlalchemy import text
from pandas.core.methods.to_dict import to_dict
import json

@st.cache_data(ttl=60)
def init_db():
    conn = st.connection('versions_db', type='sql')
    with conn.session as s:
        s.execute(text(
            'CREATE TABLE IF NOT EXISTS versions (id TEXT, browser TEXT, channel TEXT, version TEXT, success_check TEXT, fail_check TEXT, error_message TEXT);'))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
            SELECT 'chrome_stable', 'chrome', 'stable', '', '0', '0', ''
            WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'chrome_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'edge_stable', 'edge', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'edge_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'firefox_stable', 'firefox', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'firefox_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'safari_stable', 'safari', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'safari_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opi_stable', 'opi', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opi_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opa_stable', 'opa', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opa_stable');"""
        ))
        s.execute(text(
            """INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message)
               SELECT 'opw_stable', 'opw', 'stable', '', '0', '0', ''
               WHERE NOT EXISTS (SELECT 1 FROM versions WHERE id = 'opw_stable');"""
        ))
        s.commit()

# Set up our database connection
@st.cache_data(ttl=60)
def db_dict():
    conn = st.connection('versions_db', type='sql', ttl=60)

    # Query the database, which returns a pandas dataframe, then convert it to a dict
    versions = conn.query('select * from versions')
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
    url = 'https://play.google.com/store/apps/details?id=com.onepassword.android'
    # response = requests.get(url)
    # soup = BeautifulSoup(response.content, 'html.parser')

    # Placeholder so that should_we_scrape functions as expected
    conn = st.connection('versions_db', type='sql')
    fail_time = datetime.now().timestamp()
    error_msg = "Not checking yet"
    with conn.session as s:
        s.execute(text(
            "UPDATE versions SET fail_check = :fail_time, error_message = :error_msg WHERE id = :app;"),
            {"fail_time": fail_time, "error_msg": error_msg, "app": "opa_stable"}, )
        s.commit()

    return

def opw_stable_scrape():
    # Placeholder so that should_we_scrape functions as expected
    conn = st.connection('versions_db', type='sql')
    fail_time = datetime.now().timestamp()
    error_msg = "Not checking yet"
    with conn.session as s:
        s.execute(text(
            "UPDATE versions SET fail_check = :fail_time, error_message = :error_msg WHERE id = :app;"),
            {"fail_time": fail_time, "error_msg": error_msg, "app": "opw_stable"}, )
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