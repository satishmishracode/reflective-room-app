import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Set page config
st.set_page_config(page_title="The Reflective Room", layout="centered")

st.title("🪞 The Reflective Room - Debug Mode")

# Google Sheets Setup
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

client = gspread.authorize(creds)

# 🔍 Debug: Show visible spreadsheets
st.subheader("🔎 Sheets visible to the service account:")
try:
    spreadsheets = client.openall()
    for s in spreadsheets:
        st.write(f"📄 {s.title}")
except Exception as e:
    st.error(f"Error listing sheets: {e}")
