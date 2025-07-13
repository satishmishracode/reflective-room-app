
import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIG --- #
SHEET_URL = "https://docs.google.com/spreadsheets/d/1kfAXeG867wu1f8sIKkGPG6wnFD2VSjxG/edit#gid=0"
ADMIN_PASSWORD = "reflect123"

# --- AUTH (load from Streamlit secrets) --- #
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL)
poems_ws = sheet.worksheet("Poems")
prompt_ws = sheet.worksheet("WeeklyPrompt")

# --- HELPER FUNCTIONS --- #
def get_poems_df():
    data = poems_ws.get_all_records()
    return pd.DataFrame(data)

def get_prompt_df():
    data = prompt_ws.get_all_records()
    return pd.DataFrame(data)

def submit_poem(data):
    poems_ws.append_row(data)

def update_featured(index):
    df = get_poems_df()
    for i in range(len(df)):
        poems_ws.update_cell(i + 2, 7, "TRUE" if i == index else "FALSE")  # Column G = Featured

def update_prompt(week, title, desc):
    prompt_ws.append_row([week, title, desc, datetime.now().strftime('%Y-%m-%d')])

# --- UI --- #
st.set_page_config(page_title="The Reflective Room", layout="centered")
menu = st.sidebar.selectbox("Navigate", ["Home", "Submit a Poem", "Admin Panel"])

if menu == "Home":
    st.title("🪞 The Reflective Room")
    st.subheader("🌿 Weekly Prompt")

    prompt_df = get_prompt_df()
    if not prompt_df.empty:
        latest = prompt_df.iloc[-1]
        st.markdown(f"**Week {latest['Week Number']}** — *{latest['Prompt Title']}*")
        st.write(latest['Description'])
    else:
        st.info("No prompt posted yet.")

    st.subheader("🌟 Featured Poem")
    poems_df = get_poems_df()
    featured = poems_df[poems_df['Featured'] == "TRUE"]
    if not featured.empty:
        poem = featured.iloc[0]
        st.markdown(f"### {poem['Poem Title']}")
        st.write(poem['Poem Text'])
        if poem['Name']:
            st.markdown(f"*– {poem['Name']}*")
    else:
        st.info("No poem featured yet.")

elif menu == "Submit a Poem":
    st.title("📝 Submit a Poem")
    with st.form("poem_form"):
        name = st.text_input("Your Name (optional)")
        ig = st.text_input("Instagram Handle (optional)")
        title = st.text_input("Poem Title")
        poem = st.text_area("Poem Text")
        theme = st.text_input("Theme (optional)")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if title and poem:
                submit_poem([name, ig, title, poem, theme, datetime.now().strftime("%Y-%m-%d"), "FALSE"])
                st.success("Poem submitted successfully.")
            else:
                st.error("Poem Title and Text are required.")

elif menu == "Admin Panel":
    st.title("🔐 Admin Panel")
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == ADMIN_PASSWORD:
        st.success("Access granted.")
        poems_df = get_poems_df()
        st.subheader("📋 All Submissions")
        st.dataframe(poems_df)

        st.subheader("🌟 Feature a Poem")
        index = st.selectbox("Select a poem to feature", poems_df.index, format_func=lambda i: poems_df.at[i, 'Poem Title'])
        if st.button("Mark as Featured"):
            update_featured(index)
            st.success("Poem marked as featured.")

        st.subheader("🆕 Post New Prompt")
        with st.form("prompt_form"):
            week = st.number_input("Week Number", min_value=1, step=1)
            title = st.text_input("Prompt Title")
            desc = st.text_area("Prompt Description")
            post = st.form_submit_button("Post Prompt")
            if post:
                update_prompt(week, title, desc)
                st.success("Prompt posted.")
    else:
        st.warning("Enter valid password to access admin features.")
