import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="The Reflective Room", layout="wide")

# ---------- Custom CSS for Better UI ----------
st.markdown("""
<style>
.big-title {
    font-size: 36px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 10px;
}
.subtle {
    font-size: 16px;
    color: #555;
    text-align: center;
    margin-bottom: 30px;
}
.section {
    border-top: 1px solid #eee;
    margin-top: 40px;
    padding-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<div class="big-title">🪞 The Reflective Room</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">A space to reflect, express, and connect — one poem at a time.</div>', unsafe_allow_html=True)

# ---------- Google Sheets Setup ----------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
    spreadsheet = client.open_by_key(sheet_id)

    worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
    target_title = next((title for title in worksheet_titles if title.strip().lower() == "submissions"), None)

    if not target_title:
        st.error("❌ Worksheet named 'Submissions' not found.")
    else:
        worksheet = spreadsheet.worksheet(target_title)

        # ---------- Submit Section ----------
        st.markdown('<div class="section"></div>', unsafe_allow_html=True)
        st.markdown("### 📬 Submit Your Poem")

        col1, col2 = st.columns([2, 1])
        with col2:
            st.metric("📚 Total Poems", len(worksheet.get_all_values()) - 1)

        records = worksheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            poet_counts = df['name'].value_counts().reset_index()
            poet_counts.columns = ['Poet', 'Poems Submitted']

            with col1:
                st.subheader("🧾 Poem Count by Poet")
                st.dataframe(poet_counts, use_container_width=True)

        # ---------- Form Section ----------
        st.markdown('<div class="section"></div>', unsafe_allow_html=True)
        st.markdown("### ✍️ Share Your Reflection")

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