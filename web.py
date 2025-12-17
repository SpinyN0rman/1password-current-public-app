import streamlit as st
from pandas.core.methods.to_dict import to_dict
from sqlalchemy import text

conn = st.connection('versions_db', type='sql')

with conn.session as s:
    s.execute(text('CREATE TABLE IF NOT EXISTS versions (id TEXT, browser TEXT, channel TEXT, version TEXT, success_check TEXT, fail_check TEXT, error_message TEXT);'))
    s.execute(text('DELETE FROM versions;'))
    browsers = {'chrome_stable': ['chrome', 'stable', '8.11.22', '2025-12-17:10:18', '', ''], 'edge_stable': ['edge', 'stable', '8.11.22', '2025-12-17:10:18', '', ''], 'firefox_stable': ['firefox', 'stable', '8.11.16', '2025-11-10:06:10', '2025-12-17:10:18', 'scrape failed']}
    for k in browsers:
        s.execute(text(
            'INSERT INTO versions (id, browser, channel, version, success_check, fail_check, error_message) VALUES (:id, :browser, :channel, :version, :success_check, :fail_check, :error_message);'),
            params=dict(id=k, browser=browsers[k][0], channel=browsers[k][1], version=browsers[k][2], success_check=browsers[k][3], fail_check=browsers[k][4], error_message=browsers[k][5])
        )
    s.commit()

# Query and display the data you inserted
versions = conn.query('select * from versions')
st.dataframe(versions)
versions_dict = to_dict(versions, orient='index')

cols = st.columns(len(versions_dict), border=True)

for index, col in enumerate(cols):
    with col:
        # for version, index in enumerate(versions_dict):
        # flex = st.container(border=True, horizontal=True, horizontal_alignment="right")
        if versions_dict[index]['fail_check'] == "":
            fail_indicator = "🟢"
        else:
            fail_indicator = "🔴"
        title1, title2 = st.columns([0.9,0.1], vertical_alignment="center")
        with title1:
            st.subheader(f"{versions_dict[index]['browser']}")
        with title2:
            st.write(f"{fail_indicator}")
        st.caption(f"*{versions_dict[index]['channel']}*")
        st.write(f"**Version: `{versions_dict[index]['version']}`**")
        st.write(f"*Last successful check: **{versions_dict[index]['success_check']}***")
        if versions_dict[index]['fail_check'] != "":
            st.write(f"*Last failed check: **{versions_dict[index]['fail_check']}** "
                     f"with error message: **{versions_dict[index]['error_message']}***")