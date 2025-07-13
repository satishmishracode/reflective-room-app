import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="The Reflective Room", page_icon="🪞")

st.title("🪞 The Reflective Room")
st.subheader("Submit your poem below and be part of our weekly reflections.")

# --- Google Sheets Auth ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# --- Google Sheet Access ---
SHEET_ID = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
WORKSHEET_NAME = "Submissions"

try:
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)
except Exception as e:
    st.error(f"❌ Could not open Google Sheet: {e}")
    st.stop()

# --- Submission Form ---
with st.form("poem_form"):
    name = st.text_input("Your Name")
    instagram = st.text_input("Instagram Handle (optional)")
    poem = st.text_area("Your Poem", height=200)
    submit = st.form_submit_button("Submit")

    if submit:
        if not name or not poem:
            st.warning("⚠️ Please fill in both your name and your poem.")
        else:
            worksheet.append_row([name, instagram, poem])
            st.success("✅ Your poem has been submitted successfully!")