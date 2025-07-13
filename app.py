import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from admin import show_admin_page  # admin.py should be in the same folder

# ----------------- App Layout -----------------
st.set_page_config(page_title="The Reflective Room", layout="centered")
st.sidebar.title("🪞 The Reflective Room")
page = st.sidebar.selectbox("Go to", ["Submit Poem", "Admin View"])

# ----------------- Google Sheet Setup -----------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Load service account key and connect
creds = Credentials.from_service_account_file("reflective-room-service-account.json", scopes=scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open_by_key("1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM")
worksheet = sheet.worksheet("Submissions")

# ----------------- Submit Poem Page -----------------
if page == "Submit Poem":
    st.title("📬 Submit Your Poem")
    
    with st.form("submission_form"):
        name = st.text_input("Your Name")
        poem = st.text_area("Your Poem")
        submit = st.form_submit_button("Submit")
        
        if submit:
            if name.strip() == "" or poem.strip() == "":
                st.warning("Please fill in both fields.")
            else:
                worksheet.append_row([name, poem])
                st.success("✅ Poem submitted successfully!")

# ----------------- Admin View -----------------
elif page == "Admin View":
    show_admin_page()