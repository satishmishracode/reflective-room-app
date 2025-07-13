import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="The Reflective Room", layout="centered")

st.title("🪞 The Reflective Room")
st.markdown("Submit your poem below and be part of our weekly reflections.")

# Google Sheets setup using Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    # Try opening the spreadsheet
    sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
    spreadsheet = client.open_by_key(sheet_id)

    st.success("✅ Connected to Google Sheet!")

    st.markdown("### 📄 Worksheets found:")
    sheets = spreadsheet.worksheets()
    for ws in sheets:
        st.write(f"- {ws.title}")

    # Form to submit poem
    st.markdown("---")
    st.subheader("📬 Submit Your Poem")

    with st.form(key="poem_form"):
        name = st.text_input("Your Name")
        poem = st.text_area("Your Poem")
        submit_button = st.form_submit_button(label="Submit")

    if submit_button and name and poem:
        try:
            worksheet = spreadsheet.worksheet("Submissions")  # Ensure tab is named "Submissions"
            worksheet.append_row([name, poem])
            st.success("🎉 Poem submitted successfully!")
        except Exception as e:
            st.error(f"⚠️ Failed to submit poem: {e}")

except Exception as e:
    st.error(f"❌ Could not connect to Google Sheet: {e}")