import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import openai

# ---------- Page Setup ----------
st.set_page_config(page_title="The Reflective Room", layout="centered")

# ---------- Title with Logo ----------
st.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; justify-content: center; padding-bottom: 10px;'>
        <img src='https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png' width='100'>
        <h2 style='margin: 0;'>The Reflective Room</h2>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("Submit your poem below and be part of our weekly reflections.")

# ---------- Google Sheets Setup ----------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    # Open spreadsheet
    sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
    spreadsheet = client.open_by_key(sheet_id)
    worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
    target_title = next((title for title in worksheet_titles if title.strip().lower() == "submissions"), None)

    if not target_title:
        st.error("❌ Worksheet named 'Submissions' not found. Please check sheet tab name.")
    else:
        worksheet = spreadsheet.worksheet(target_title)
        st.success("✅ Connected to Google Sheet!")

        # Poem Count
        st.markdown("### 📬 Submit Your Poem")
        st.info(f"📚 Total poems submitted: {len(worksheet.get_all_values()) - 1}")

        # Poet Count Table
        records = worksheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            poet_counts = df['name'].value_counts().reset_index()
            poet_counts.columns = ['Poet', 'Poems Submitted']
            st.subheader("🧾 Poem Count by Poet")
            st.dataframe(poet_counts)

        # Submission Form
        with st.form(key="poem_form"):
            name = st.text_input("Your Name")
            poem = st.text_area("Your Poem")
            submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            if name.strip() == "" or poem.strip() == "":
                st.warning("Please fill in both fields.")
            else:
                try:
                    worksheet.append_row([name, poem])

                    # ---------- OpenAI Reflection ----------
                    openai.api_key = st.secrets["openai_key"]["openai_key"]
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a poetry reviewer. Respond with a 2-line honest reflection of the poem, rate it out of 10, and highlight one most striking line."},
                            {"role": "user", "content": poem}
                        ],
                        max_tokens=150,
                        temperature=0.7
                    )

                    reply = response.choices[0].message.content.strip()
                    st.success("✅ Poem submitted successfully!")
                    st.markdown(f"### ✨ Reflection\n{reply}")

                except Exception as e:
                    st.error(f"⚠️ Failed to generate reflection: {e}")

except Exception as e:
    st.error(f"❌ Could not connect to Google Sheet: {e}")