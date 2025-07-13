import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from admin import show_admin_page

st.set_page_config(page_title="The Reflective Room", layout="centered")

st.title("🪞 The Reflective Room")
st.markdown("Submit your poem below and be part of our weekly reflections.")

st.sidebar.title("🪞 The Reflective Room")
page = st.sidebar.selectbox("Go to", ["Submit Poem", "Admin View"])



# Google Sheets setup using Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    # Open the spreadsheet by ID
    sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
    spreadsheet = client.open_by_key(sheet_id)

    st.success("✅ Connected to Google Sheet!")

    # Try to access 'Submissions' worksheet (case-insensitive check)
    worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
    target_title = None
    for title in worksheet_titles:
        if title.strip().lower() == "submissions":
            target_title = title
            break

    if not target_title:
        st.error("❌ Worksheet named 'Submissions' not found. Please check sheet tab name.")
    else:
        worksheet = spreadsheet.worksheet(target_title)

        if page == "Submit Poem":
    # your poem submission form code here
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

elif page == "Admin View":
    show_admin_page()
                except Exception as e:
                    st.error(f"⚠️ Failed to submit poem: {e}")

except Exception as e:
    st.error(f"❌ Could not connect to Google Sheet: {e}")