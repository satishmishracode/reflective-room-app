import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from openai import OpenAI
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import textwrap
import plotly.graph_objs as go

# ---------- Page Setup ----------
st.set_page_config(page_title="The Reflective Room", layout="centered")

# ---------- Title with Logo ----------
st.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; justify-content: center; padding-bottom: 5px;'>
        <img src='https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png' width='60'>
        <div>
            <h2 style='margin-bottom: 0;'>The Reflective Room</h2>
            <div style='font-size:16px;color:#666;margin-top:-8px;'>Share your soul in verse.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- Google Sheets Setup ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
worksheet_name = "Submissions"

def get_worksheet():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(worksheet_name)
    return worksheet

def get_data():
    worksheet = get_worksheet()
    data = worksheet.get_all_records()
    columns = ["name", "poem", "poem_title", "instagram_handle", "reflection_score"]
    df = pd.DataFrame(data)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df

# ---------- Poster Generation Function ----------
def generate_white_poster_with_logo(poet_name: str, poem_text: str, poem_title: str, insta_handle: str) -> str:
    img_width, img_height = 1080, 1080  # Square for Instagram carousel
    background_color = "white"
    text_color = "black"

    image = Image.new("RGB", (img_width, img_height), color=background_color)
    draw = ImageDraw.Draw(image)

    # Paste logo at top center
    logo_url = "https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png"
    try:
        resp = requests.get(logo_url)
        logo = Image.open(BytesIO(resp.content)).convert("RGBA")
        logo = logo.resize((130, int(130 * logo.height / logo.width)))
        logo_x = (img_width - logo.width) // 2
        image.paste(logo, (logo_x, 50), logo)
    except Exception:
        pass

    # Load font
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        poem_font = ImageFont.truetype(font_path, 42)
        name_font = ImageFont.truetype(font_path, 36)
        meta_font = ImageFont.truetype(font_path, 28)
    except Exception:
        poem_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    # Draw poem title
    y_cursor = 220
    if poem_title:
        title_lines = textwrap.wrap(poem_title, width=20)
        for line in title_lines:
            w, h = draw.textbbox((0,0), line, font=name_font)[2:]
            draw.text(((img_width-w)/2, y_cursor), line, font=name_font, fill="#444")
            y_cursor += h + 5
        y_cursor += 10

    # Draw poem text (up to 11 lines)
    lines = poem_text.strip().split("\n")
    for line in lines[:11]:
        wrapped_lines = textwrap.wrap(line, width=30)
        for wrap_line in wrapped_lines:
            w, h = draw.textbbox((0,0), wrap_line, font=poem_font)[2:]
            draw.text(((img_width-w)/2, y_cursor), wrap_line, font=poem_font, fill=text_color)
            y_cursor += h + 6
    y_cursor += 18

    # Poet's Instagram handle at bottom left
    if insta_handle:
        handle_text = f"@{insta_handle.strip()}"
        w, h = draw.textbbox((0,0), handle_text, font=meta_font)[2:]
        draw.text((45, img_height - h - 55), handle_text, font=meta_font, fill="#999")

    # Poet name at bottom right
    if poet_name:
        name_text = f"— {poet_name}"
        w, h = draw.textbbox((0,0), name_text, font=name_font)[2:]
        draw.text((img_width - w - 45, img_height - h - 55), name_text, font=name_font, fill="#666")

    # Save image to tmp
    tmpdir = tempfile.gettempdir()
    filename = f"{poet_name or 'poet'}_poem_poster.png"
    out_path = os.path.join(tmpdir, filename)
    image.save(out_path)
    return out_path

# ---------- Helper: Reflection Score Extraction ----------
def extract_score(reflection: str):
    import re
    matches = re.findall(r"(\d+)/10", reflection)
    if matches:
        try:
            return int(matches[0])
        except Exception:
            return 0
    return 0

# ============ MAIN APP LOGIC ============

st.markdown(" ", unsafe_allow_html=True)  # Spacer

# ------------ Poetry Submission ------------
st.markdown("### 📝 Submit Your Poem")

if "submission_successful" not in st.session_state:
    st.session_state["submission_successful"] = False
    st.session_state["submission_data"] = {}

with st.form(key="poem_form"):
    name = st.text_input("Your Name")
    poem_title = st.text_input("Poem Title (optional)")
    poem = st.text_area("Your Poem", height=180)
    insta_handle = st.text_input("Instagram Handle (optional)")
    passkey = st.text_input("Community Passkey", type="password")
    submit = st.form_submit_button("Submit")

reflection_ai = ""
reflection_score = 0

if submit:
    if not (name and poem and passkey):
        st.warning("Please fill all required fields including passkey.")
    elif passkey != st.secrets["community"]["passkey"]:
        st.error("❌ Invalid community passkey. Please contact admin.")
    else:
        try:
            worksheet = get_worksheet()
            # Generate reflection via OpenAI
            openai_client = OpenAI(api_key=st.secrets["openai_key"]["openai_key"])
            with st.spinner("The Reflective Room is listening..."):
                ai_resp = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a thoughtful poetry critic. Provide a 2-line honest reflection and rate out of 10."},
                        {"role": "user", "content": poem}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )
            reflection_ai = ai_resp.choices[0].message.content.strip()
            reflection_score = extract_score(reflection_ai)
            # Store in sheet
            worksheet.append_row([
                name,
                poem,
                poem_title,
                insta_handle,
                reflection_score
            ])
            st.success("✅ Poem submitted successfully!")
            st.session_state["submission_successful"] = True
            st.session_state["submission_data"] = {
                "name": name,
                "poem_title": poem_title,
                "poem": poem,
                "insta_handle": insta_handle
            }
            st.session_state["reflection_ai"] = reflection_ai
        except Exception as e:
            st.error(f"❌ Failed to submit: {e}")

df = get_data()

# Pie Chart of Poem Counts ("Constellation of Voices") - Plotly version
with st.expander("🌌 Constellation of Voices (Click to show)"):
    if not df.empty:
        poet_counts = df['name'].value_counts()
        st.write(f"**Total poems submitted:** {poet_counts.sum()}")
        fig = go.Figure(
            data=[go.Pie(labels=poet_counts.index, values=poet_counts.values, textinfo="label+percent", hole=0.3)],
        )
        fig.update_layout(showlegend=True, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

# Reflection Points Leaderboard Table
with st.expander("🌟 Reflection Points Leaderboard (Click to show)"):
    if not df.empty and "reflection_score" in df.columns:
        leaderboard = df.groupby("name")["reflection_score"].sum().reset_index().sort_values("reflection_score", ascending=False)
        leaderboard.columns = ["Poet", "Reflection Points"]
        st.table(leaderboard)

# ------------ AI Reflection (only after submission) ------------
if st.session_state.get("submission_successful", False):
    st.markdown("---")
    st.markdown("🔮 **The Reflective Room thinks:**")
    st.info(st.session_state.get("reflection_ai", "No reflection generated."))
    st.markdown("---")
    st.markdown("### 🖼️ Generate Your Poetry Poster(s)")

    if st.button("Generate Poetry Poster(s)"):
        submission = st.session_state["submission_data"]
        lines = submission["poem"].split("\n")
        chunk_size = 11
        poem_chunks = [ "\n".join(lines[i:i+chunk_size]) for i in range(0, len(lines), chunk_size) ]
        poster_paths = []
        for idx, chunk in enumerate(poem_chunks):
            poster_path = generate_white_poster_with_logo(submission["name"], chunk, submission["poem_title"], submission["insta_handle"])
            poster_paths.append(poster_path)
            st.image(poster_path, caption=f"Poetry Poster {idx+1}", use_column_width=True)
        # Download all as zip
        import zipfile
        from io import BytesIO
        if len(poster_paths) > 0:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for path in poster_paths:
                    with open(path, "rb") as f:
                        zipf.writestr(os.path.basename(path), f.read())
            st.download_button(
                label=f"Download All Poster{'s' if len(poster_paths)>1 else ''} (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="ReflectiveRoom_PoetryPosters.zip",
                mime="application/zip"
            )

st.markdown("---")
st.caption("Crafted with ❤️ for poets, writers, and seekers.")

