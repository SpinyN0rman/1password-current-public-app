import streamlit as st
import functions as func

st.set_page_config(layout="wide")

# Initialise the database, if it doesn't already exist
func.init_db()
func.init_playwright()

# Scrape if the last check was more than an hour ago
perform_scrape = func.should_we_scrape()
if perform_scrape:
    func.edge_stable_api()
    func.chrome_stable_scrape()
    func.firefox_stable_scrape()
    func.safari_stable_scrape()
    func.opi_stable_scrape()
    func.opa_stable_scrape()
    func.opw_stable_scrape()
    func.opm_stable_scrape()

# Clear Streamlit's caches
st.cache_data.clear()
st.cache_resource.clear()

# Fetches a dictionary from the database
ext_versions_dict = func.db_dict("browser_extension")
ext_container = st.container(width=250*len(ext_versions_dict))

with ext_container:
    st.header("Browser Extensions")

    ext_cols = st.columns(len(ext_versions_dict), border=True)

    for index, col in enumerate(ext_cols):
        with col:
            if ext_versions_dict[index]['success_check'] > ext_versions_dict[index]['fail_check']:
                fail_indicator = "🟢"
            else:
                fail_indicator = "🔴"
            st.subheader(f"{func.format_name(ext_versions_dict[index]['browser'])}")
            st.caption(f"*{ext_versions_dict[index]['channel']}*")
            st.write(f"**Version: `{ext_versions_dict[index]['version']}`**")
            if ext_versions_dict[index]['success_check'] != "0":
                st.write(f"{fail_indicator} *Last successful check: **{func.format_datetime(ext_versions_dict[index]['success_check'])}***")
            if ext_versions_dict[index]['fail_check'] > ext_versions_dict[index]['success_check']:
                st.write(f"{fail_indicator} *Last failed check: **{func.format_datetime(ext_versions_dict[index]['fail_check'])}** "
                         f"with error message: **{ext_versions_dict[index]['error_message']}***")

# Fetches a dictionary from the database
mobile_versions_dict = func.db_dict("mobile")
mobile_container = st.container(width=250*len(mobile_versions_dict))

with mobile_container:
    st.header("Mobile Apps")

    mobile_cols = st.columns(len(mobile_versions_dict), border=True)

    for index, col in enumerate(mobile_cols):
        with col:
            if mobile_versions_dict[index]['success_check'] > mobile_versions_dict[index]['fail_check']:
                fail_indicator = "🟢"
            else:
                fail_indicator = "🔴"
            st.subheader(f"{func.format_name(mobile_versions_dict[index]['browser'])}")
            st.caption(f"*{mobile_versions_dict[index]['channel']}*")
            st.write(f"**Version: `{mobile_versions_dict[index]['version']}`**")
            if mobile_versions_dict[index]['success_check'] != "0":
                st.write(f"{fail_indicator} *Last successful check: **{func.format_datetime(mobile_versions_dict[index]['success_check'])}***")
            if mobile_versions_dict[index]['fail_check'] > mobile_versions_dict[index]['success_check']:
                st.write(f"{fail_indicator} *Last failed check: **{func.format_datetime(mobile_versions_dict[index]['fail_check'])}** "
                         f"with error message: **{mobile_versions_dict[index]['error_message']}***")

# Fetches a dictionary from the database
desktop_versions_dict = func.db_dict("desktop")
desktop_container = st.container(width=250*len(desktop_versions_dict))

with desktop_container:
    st.header("Desktop Apps")

    desktop_cols = st.columns(len(desktop_versions_dict), border=True)

    for index, col in enumerate(desktop_cols):
        with col:
            if desktop_versions_dict[index]['success_check'] > desktop_versions_dict[index]['fail_check']:
                fail_indicator = "🟢"
            else:
                fail_indicator = "🔴"
            st.subheader(f"{func.format_name(desktop_versions_dict[index]['browser'])}")
            st.caption(f"*{desktop_versions_dict[index]['channel']}*")
            st.write(f"**Version: `{desktop_versions_dict[index]['version']}`**")
            if desktop_versions_dict[index]['success_check'] != "0":
                st.write(f"{fail_indicator} *Last successful check: **{func.format_datetime(desktop_versions_dict[index]['success_check'])}***")
            if desktop_versions_dict[index]['fail_check'] > desktop_versions_dict[index]['success_check']:
                st.write(f"{fail_indicator} *Last failed check: **{func.format_datetime(desktop_versions_dict[index]['fail_check'])}** "
                         f"with error message: **{desktop_versions_dict[index]['error_message']}***")
