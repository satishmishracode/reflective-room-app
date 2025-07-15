import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import textwrap
import math
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from openai import OpenAI
import zipfile
import os

# ---------- Page Setup ----------
st.set_page_config(page_title="The Reflective Room", layout="centered")

# ---------- Title with Logo ----------
st.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; justify-content: center; padding-bottom: 10px;'>
        <img src='https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png' width='90'>
        <h2 style='margin: 0;'>The Reflective Room</h2>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("Share your soul in verse.")

# ---------- Google Sheets Setup ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ---------- Poster Generation (Square) ----------
def generate_square_posters(poet_name: str, poem_text: str, max_lines_per_img=11):
    IMG_WIDTH, IMG_HEIGHT = 1080, 1080
    BACKGROUND_COLOR = "white"
    TEXT_COLOR = "black"
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_SIZE = 42
    LINE_SPACING = 10
    MARGIN = 80
    TOP_PADDING = 180

    # Load font
    try:
        poem_font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        name_font = ImageFont.truetype(FONT_PATH, 36)
    except Exception:
        poem_font = ImageFont.load_default()
        name_font = ImageFont.load_default()

    # Split into lines
    poem_lines = []
    for original_line in poem_text.split("\n"):
        if original_line.strip():
            wrapped = textwrap.wrap(original_line, width=30)
            poem_lines.extend(wrapped)
        else:
            poem_lines.append("")  # preserve blank lines

    # Split into chunks for multiple images
    poster_paths = []
    total_lines = len(poem_lines)
    num_images = (total_lines + max_lines_per_img - 1) // max_lines_per_img

    for i in range(num_images):
        lines = poem_lines[i*max_lines_per_img : (i+1)*max_lines_per_img]
        image = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        # Logo at top
        logo_url = "https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png"
        try:
            response = requests.get(logo_url)
            logo = Image.open(BytesIO(response.content)).convert("RGBA")
            logo = logo.resize((150, int(150 * logo.height / logo.width)))
            logo_x = (IMG_WIDTH - logo.width) // 2
            image.paste(logo, (logo_x, 25), logo)
        except Exception:
            pass

        # Draw poem lines
        y = TOP_PADDING
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=poem_font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((IMG_WIDTH - w) / 2, y), line, font=poem_font, fill=TEXT_COLOR)
            y += h + LINE_SPACING

        # On last image, add poet's name
        if i == num_images - 1 and poet_name:
            name_text = f"— {poet_name}"
            bbox = draw.textbbox((0, 0), name_text, font=name_font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((IMG_WIDTH - w - MARGIN, IMG_HEIGHT - h - 60), name_text, font=name_font, fill="gray")

        # Save poster
        poster_path = f"/tmp/reflective_room_poem_poster_{i+1}.png"
        image.save(poster_path)
        poster_paths.append(poster_path)

    return poster_paths

# ---------- Main App Logic ----------
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet("Submissions")
    st.success("✅ Google Sheet connected!")

    st.markdown("### 📬 Submit Your Poem")
    total = len(worksheet.get_all_values()) - 1
    st.info(f"📚 Total poems submitted: {total}")

    records = worksheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        counts = df['name'].value_counts().reset_index()
        counts.columns = ['Poet', 'Poems Submitted']
        st.subheader("🧾 Poem Count by Poet")
        st.dataframe(counts)

    with st.form("poem_form"):
        name = st.text_input("Your Name")
        poem = st.text_area("Your Poem")
        passkey = st.text_input("Reflective Room Passkey", type="password")
        submit = st.form_submit_button("Submit")

    if submit:
        correct_passkey = st.secrets["community"]["passkey"]
        if not name.strip() or not poem.strip():
            st.warning("Please fill in both fields.")
        elif passkey != correct_passkey:
            st.error("Incorrect community passkey. Please ask the admin for the latest passcode.")
        else:
            worksheet.append_row([name, poem])
            st.success("✅ Poem submitted successfully!")

            openai_client = OpenAI(api_key=st.secrets["openai_key"]["openai_key"])
            with st.spinner("🪞 The Reflective Room soul is listening..."):
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a thoughtful poetry critic. Provide a 2-line honest reflection and rate out of 10."},
                        {"role": "user", "content": poem}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
            reflection = response.choices[0].message.content.strip()
            st.markdown("---")
            st.markdown("**The Reflective Room Thinks:**")
            st.info(reflection)

            # Generate posters (splits into multiple images if needed)
            poster_paths = generate_square_posters(name, poem)

            # Display all posters
            st.subheader("✨ Your Poetry Poster(s)")
            for path in poster_paths:
                st.image(path, use_column_width=True)

            # Offer a ZIP download of all posters
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for idx, path in enumerate(poster_paths):
                    zipf.write(path, os.path.basename(path))
            zip_buffer.seek(0)
            st.download_button(
                label="Download All Posters (ZIP)",
                data=zip_buffer,
                file_name="reflective_room_poetry_posters.zip",
                mime="application/zip"
            )

except Exception as e:
    st.error(f"❌ Error: {e}")