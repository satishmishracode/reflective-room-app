import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="The Reflective Room", layout="centered")

st.title("🪞 The Reflective Room")
st.markdown("Submit your poem below and be part of our weekly reflections.")

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

    # Locate 'Submissions' worksheet
    worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
    target_title = next((title for title in worksheet_titles if title.strip().lower() == "submissions"), None)

    if not target_title:
        st.error("❌ Worksheet named 'Submissions' not found. Please check sheet tab name.")
    else:
        worksheet = spreadsheet.worksheet(target_title)

        # Display total poem count
        st.markdown("### 📬 Submit Your Poem")
        st.info(f"📚 Total poems submitted: {len(worksheet.get_all_values()) - 1}")

        # Display poet-wise counts
        records = worksheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            poet_counts = df['name'].value_counts().reset_index()
            poet_counts.columns = ['Poet', 'Poems Submitted']

            st.subheader("🧾 Poem Count by Poet")
            st.dataframe(poet_counts)

        # Submission form
        with st.form(key="poem_form"):
            name = st.text_input("Your Name")
            poem = st.text_area("Your Poem")
            submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            try:
                if name.strip() == "" or poem.strip() == "":
                    st.warning("Please fill in both fields.")
                else:
                    worksheet.append_row([name, poem])
                    st.balloons()
                    st.success("✅ Poem submitted successfully!")
                    st.markdown(f"""
---
🕊️ **Thank you, _{name}_!**  
Your words have joined a growing constellation of reflections.  
Keep writing. Keep feeling. Keep shining. 🌙✨
""")
            except Exception as e:
                st.error(f"⚠️ Failed to submit poem: {e}")

except Exception as e:
    st.error(f"❌ Could not connect to Google Sheet: {e}")