import streamlit as st
from pandas.core.methods.to_dict import to_dict
import functions as func

st.set_page_config(layout="wide")

# Initialise the database, if it doesn't already exist
func.init_db()

# Scrape if the last check was more than an hour ago
perform_scrape = func.should_we_scrape()
if perform_scrape:
    func.edge_stable_api()
    func.chrome_stable_scrape()
    # Now clear Streamlit's caches
    st.cache_data.clear()
    st.cache_resource.clear()

# Fetches a dictionary from the database
versions_dict = func.db_dict()

cols = st.columns(len(versions_dict), border=True)

for index, col in enumerate(cols):
    with col:
        if versions_dict[index]['success_check'] > versions_dict[index]['fail_check']:
            fail_indicator = "🟢"
        else:
            fail_indicator = "🔴"
        st.subheader(f"{versions_dict[index]['browser']}")
        st.caption(f"*{versions_dict[index]['channel']}*")
        st.write(f"**Version: `{versions_dict[index]['version']}`**")
        if versions_dict[index]['success_check'] == "0":
            st.write("*Not checking yet*")
        else:
            st.write(f"{fail_indicator} *Last successful check: **{func.format_datetime(versions_dict[index]['success_check'])}***")
        if versions_dict[index]['fail_check'] > versions_dict[index]['success_check']:
            st.write(f"*Last failed check: **{versions_dict[index]['fail_check']}** "
                     f"with error message: **{versions_dict[index]['error_message']}***")