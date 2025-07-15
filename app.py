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
# (EXISTING CODE FOR POSTER FUNCTION - NO CHANGES MADE)
def generate_white_poster_with_logo(poet_name: str, poem_text: str, poem_title: str, insta_handle: str) -> str:
    img_width, img_height = 1080, 1080
    background_color = "white"
    text_color = "black"

    image = Image.new("RGB", (img_width, img_height), color=background_color)
    draw = ImageDraw.Draw(image)

    logo_url = "https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png"
    try:
        resp = requests.get(logo_url)
        logo = Image.open(BytesIO(resp.content)).convert("RGBA")
        logo = logo.resize((130, int(130 * logo.height / logo.width)))
        logo_x = (img_width - logo.width) // 2
        image.paste(logo, (logo_x, 50), logo)
    except Exception:
        pass

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        poem_font = ImageFont.truetype(font_path, 42)
        name_font = ImageFont.truetype(font_path, 36)
        meta_font = ImageFont.truetype(font_path, 28)
    except Exception:
        poem_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    y_cursor = 220
    if poem_title:
        title_lines = textwrap.wrap(poem_title, width=20)
        for line in title_lines:
            w, h = draw.textbbox((0,0), line, font=name_font)[2:]
            draw.text(((img_width-w)/2, y_cursor), line, font=name_font, fill="#444")
            y_cursor += h + 5
        y_cursor += 10

    lines = poem_text.strip().split("\n")
    for line in lines[:11]:
        wrapped_lines = textwrap.wrap(line, width=30)
        for wrap_line in wrapped_lines:
            w, h = draw.textbbox((0,0), wrap_line, font=poem_font)[2:]
            draw.text(((img_width-w)/2, y_cursor), wrap_line, font=poem_font, fill=text_color)
            y_cursor += h + 6
    y_cursor += 18

    if insta_handle:
        handle_text = f"@{insta_handle.strip()}"
        w, h = draw.textbbox((0,0), handle_text, font=meta_font)[2:]
        draw.text((45, img_height - h - 55), handle_text, font=meta_font, fill="#999")

    if poet_name:
        name_text = f"— {poet_name}"
        w, h = draw.textbbox((0,0), name_text, font=name_font)[2:]
        draw.text((img_width - w - 45, img_height - h - 55), name_text, font=name_font, fill="#666")

    tmpdir = tempfile.gettempdir()
    filename = f"{poet_name or 'poet'}_poem_poster.png"
    out_path = os.path.join(tmpdir, filename)
    image.save(out_path)
    return out_path

# ---------- Helper: Reflection Score Extraction (NO CHANGE) ----------
def extract_score(reflection: str):
    import re
    matches = re.findall(r"(\d+)/10", reflection)
    if matches:
        try:
            return int(matches[0])
        except Exception:
            return 0
    return 0

# ============ EXISTING MAIN LOGIC (NO CHANGES) ============
# (Keep existing main app logic exactly as you have.)

# ... (Your existing main app logic remains here) ...

# ========= 🎧 NEW AUDIO GENERATION FEATURE ==========
with st.expander("🎙️ Voice of Your Poem (Generate Audio)"):
    poem_text_for_audio = st.text_area("Paste your poem here to generate audio:", height=180)
    
    if st.button("✨ Generate Poem Audio"):
        if poem_text_for_audio.strip():
            with st.spinner("The Reflective Room is giving voice to your poem..."):
                try:
                    import openai
                    client = openai.OpenAI(api_key=st.secrets["openai_key"]["openai_key"])
                    
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=poem_text_for_audio
                    )

                    audio_path = os.path.join(tempfile.gettempdir(), "poem_audio.mp3")
                    response.stream_to_file(audio_path)

                    audio_file = open(audio_path, "rb")
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")

                    st.download_button(
                        label="⬇️ Download Poem Audio",
                        data=audio_bytes,
                        file_name="ReflectiveRoom_Poem_Audio.mp3",
                        mime="audio/mp3"
                    )

                except Exception as e:
                    st.error(f"❌ Failed to generate audio: {e}")
        else:
            st.warning("Please paste or write your poem above before generating audio.")

st.markdown("---")
st.caption("Crafted with ❤️ for poets, writers, and seekers.")