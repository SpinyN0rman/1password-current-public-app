import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import streamlit as st
from sqlalchemy import text
from pandas.core.methods.to_dict import to_dict

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
        if current_epoch > success_next_check or current_epoch > fail_next_check:
            return True

    return False

def format_datetime(date_time):
    utc_time = datetime.fromtimestamp(float(date_time), timezone.utc)
    local_time = utc_time.astimezone()
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M')
    return formatted_time

def edge_stable_api():
    url = 'https://microsoftedge.microsoft.com/addons/getproductdetailsbycrxid/dppgmdbiimibapkepcbdbmkaabgiofem?hl=en-US'
    try:
        response = requests.get(url)
        response_json = response.json()
        version = response_json['version']
        success_time = datetime.now().timestamp()
        fail_time = ""
        error_msg = ""
    except Exception as e:
        version = ""
        success_time = ""
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
    return


# chrome beta: https://chromewebstore.google.com/detail/1password-beta-%E2%80%93-password/khgocmkkpikpnmmkgmdnfckapcdkgfaf
# chrome nightly: https://chromewebstore.google.com/detail/1password-nightly-%E2%80%93-passw/gejiddohjgogedgjnonbofjigllpkmbf
# firefox stable: https://addons.mozilla.org/en-US/firefox/addon/1password-x-password-manager/
# firefox beta: https://c.1password.com/dist/1P/b5x/firefox/beta/updates.json
# firefox nightly: https://c.1password.com/dist/1P/b5x/firefox/nightly/updates.json
# safari: https://itunes.apple.com/lookup?bundleId=%s com.1password.safari
# opi: https://itunes.apple.com/lookup?bundleId=%s com.1password.1password
# opa:
# opw: