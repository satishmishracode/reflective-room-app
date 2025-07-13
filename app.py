
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Config
st.set_page_config(page_title="The Reflective Room - Debug", layout="centered")

# Connect to Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

st.title("🪞 The Reflective Room — Debug Mode")
st.subheader("📋 Verifying Google Sheets Access")

# Try listing all accessible spreadsheets
try:
    st.markdown("### 📚 Sheets visible to the service account:")
    sheet_list = client.openall()
    if sheet_list:
        for sheet in sheet_list:
            st.write("✅", sheet.title)
    else:
        st.warning("⚠️ No sheets found — double check sharing & permissions.")
except Exception as e:
    st.error(f"❌ Error listing sheets: {e}")

# Manual test to access a known sheet
st.markdown("### 🔍 Manual Sheet Access Test")
try:
    sheet = client.open("The Reflective Room Submissions").sheet1
    st.success("✅ Successfully opened the sheet.")
    data = sheet.get_all_values()
    st.write("📄 Sheet Content (first 2 rows):", data[:2])
except Exception as e:
    st.error(f"❌ Error accessing the sheet directly: {e}")
