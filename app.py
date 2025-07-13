
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Page config
st.set_page_config(page_title="The Reflective Room", layout="centered")

st.title("📝 The Reflective Room - Submit Your Poem")

# Google Sheets setup
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("Reflective Room Submissions").sheet1

# Submission form
with st.form("poem_form"):
    name = st.text_input("Your Name (optional)")
    poem = st.text_area("Write your 4–8 line poem here ✍️", height=200)
    submitted = st.form_submit_button("Submit")

    if submitted:
        if poem.strip() == "":
            st.warning("Poem cannot be empty.")
        else:
            sheet.append_row([name, poem])
            st.success("Thank you for submitting your poem! 🌿")

# Footer
st.markdown("---")
st.caption("✨ Powered by The Reflective Room • @the_reflectiveroom")
