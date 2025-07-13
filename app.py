import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Set page config
st.set_page_config(page_title="The Reflective Room", layout="centered")

st.title("🪞 The Reflective Room")
st.subheader("Submit your poem below and be part of our weekly reflections.")

# Google Sheets Setup
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

# ✅ Use st.secrets directly without json.loads
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("The Reflective Room Submissions").sheet1  # Change sheet name if needed

# Submission form
with st.form("poetry_form"):
    name = st.text_input("Your Name (or write 'Anonymous')", max_chars=50)
    poem = st.text_area("Your Poem", height=200)
    submit = st.form_submit_button("Submit")

    if submit:
        if not poem.strip():
            st.warning("Please write a poem before submitting.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, name, poem])
            st.success("🌟 Your poem has been submitted successfully!")

# Admin view (Optional - comment this out later)
st.markdown("---")
with st.expander("🔐 Admin Access (view submissions)"):
    if st.text_input("Enter Admin Code") == st.secrets["admin_code"]:
        st.write("📜 All Submissions:")
        data = sheet.get_all_records()
        for row in reversed(data):
            st.markdown(f"**{row['Name']}** wrote at *{row['Timestamp']}*:")
            st.code(row["Poem"])
            st.markdown("---")
