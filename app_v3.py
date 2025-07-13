# v1.2 – Timestamp patch added to force GitHub refresh

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Title and subtitle
st.set_page_config(page_title="The Reflective Room", layout="centered")
st.title("🪞 The Reflective Room")
st.subheader("Submit your poem below and be part of our weekly reflections.")

# Authenticate with Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open the target Google Sheet by name
SHEET_NAME = "The Reflective Room Submissions"
try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"Could not open Google Sheet: {e}")
    st.stop()

# Submission form
with st.form("poetry_form"):
    name = st.text_input("Your Name (Optional)")
    poem = st.text_area("Your Poem", height=300)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Harmless timestamp (not used)
    submit = st.form_submit_button("Submit")

    if submit:
        if poem.strip() == "":
            st.warning("Please write a poem before submitting.")
        else:
            # Add submission to Google Sheet
            sheet.append_row([name, poem])
            st.success("✅ Your poem has been submitted. Thank you!")

# Footer
st.markdown("---")
st.caption("🌙 Powered by The Reflective Room · Streamlit App")
