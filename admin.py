
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def show_admin_page():
    st.title("🔐 Admin Panel — Submitted Poems")

    # Ask for password
    password = st.text_input("Enter admin password", type="password")

    if password != "reflect2025":
        st.warning("Please enter the correct password to access submissions.")
        return

    # Connect to Google Sheet if password is correct
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_file("reflective-room-service-account.json", scopes=scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key("1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM")
        worksheet = sheet.worksheet("Submissions")
        data = worksheet.get_all_records()

        if data:
            df = pd.DataFrame(data)
            st.success("✅ Fetched submitted poems successfully!")
            st.dataframe(df)
        else:
            st.info("No submissions yet.")

    except Exception as e:
        st.error(f"⚠️ Error loading submissions: {e}")
