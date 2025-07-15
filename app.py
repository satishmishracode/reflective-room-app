import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
import tempfile
import os

# ---------- Page Setup ----------
st.set_page_config(page_title="The Reflective Room", layout="centered")
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Georgia', serif;
            background: #faf7f2;
        }
        .block-container {padding-top:2rem;}
        h2, h3, h4 { color: #54416d; font-family: 'Georgia', serif; }
        .main .stButton > button {border-radius: 8px; background: #7d6a97; color: white;}
    </style>
""", unsafe_allow_html=True)

# ---------- Title with Logo & Tagline ----------
st.markdown(
    """
    <div style='display: flex; align-items: center; gap: 18px; justify-content: center; padding-bottom: 8px;'>
        <img src='https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png' width='70'>
        <div>
            <h2 style='margin-bottom:0;'>The Reflective Room</h2>
            <div style='font-size:1.05rem; color:#7a6c8b; font-family:Georgia,serif;'>Share your soul in verse</div>
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

# ---------- Helper: Poster Generation ----------
def generate_white_poster_with_logo(poet_name: str, poem_text: str, img_number=1) -> str:
    """
    Creates a vertical white-background poster with the poem, poet name, and the Reflective Room logo.
    Returns the file path of the generated poster image (in /tmp).
    """
    img_width, img_height = 1080, 1080
    background_color = "white"
    text_color = "black"

    # Create canvas
    image = Image.new("RGB", (img_width, img_height), color=background_color)
    draw = ImageDraw.Draw(image)

    # Paste logo at top center
    logo_url = "https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png"
    try:
        resp = requests.get(logo_url)
        logo = Image.open(BytesIO(resp.content)).convert("RGBA")
        logo = logo.resize((170, int(170 * logo.height / logo.width)))
        logo_x = (img_width - logo.width) // 2
        image.paste(logo, (logo_x, 45), logo)
    except Exception:
        pass

    # Load font (Georgia, fallback to DejaVu)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    try:
        poem_font = ImageFont.truetype(font_path, 46)
        name_font = ImageFont.truetype(font_bold_path, 36)
    except Exception:
        poem_font = ImageFont.load_default()
        name_font = ImageFont.load_default()

    # Wrap and draw poem text (centered)
    margin = 90
    top_text_y = 260
    wrapper = textwrap.TextWrapper(width=32)
    wrapped = wrapper.wrap(poem_text)
    for line in wrapped:
        w, h = draw.textbbox((0, 0), line, font=poem_font)[2:]
        draw.text(((img_width - w) / 2, top_text_y), line, font=poem_font, fill=text_color)
        top_text_y += h + 9

    # Draw poet name at bottom right
    if poet_name:
        name_text = f"— {poet_name}"
        w, h = draw.textbbox((0, 0), name_text, font=name_font)[2:]
        draw.text((img_width - w - margin, img_height - h - 70), name_text, font=name_font, fill="#888888")

    # Save poster (always unique file)
    poster_path = f"/tmp/reflective_room_poem_poster_{img_number}.png"
    image.save(poster_path)
    return poster_path

# ---------- Main App Logic ----------
try:
    # Authorize Google Sheets
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet_id = "1-BdTHzj1VWqz45G9kCwQ1cjZxzKZG9KP3SAaxYycUaM"
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet("Submissions")

    # Display stats (no connection message!)
    st.markdown("""
        <div style='margin-top:1em;'></div>
        <div style='background:#f3f1fa; border-radius:12px; padding:18px 10px 12px 18px; margin-bottom:18px; box-shadow:0 1px 5px #e4def7;'>
            <h4 style='color:#51456a;font-family:Georgia,serif; margin-bottom:5px;'>📬 Submit Your Poem</h4>
            <div style='font-size:1.03rem;color:#837ea7;'><b>🌟 Total poems submitted: {}</b></div>
        </div>
    """.format(len(worksheet.get_all_values())-1), unsafe_allow_html=True)

    records = worksheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        # Poem count by poet - Pie chart
        with st.container():
            st.markdown(
                "<div style='background:#f5f2ff; border-radius:13px; box-shadow:0 1px 5px #e7e2fa; padding:16px 8px; margin-bottom:14px;'><i style='color:#8e7dc1;'>🌌 Constellation of Voices</i></div>",
                unsafe_allow_html=True
            )
            counts = df['name'].value_counts()
            fig, ax = plt.subplots(figsize=(4.5,4.5))
            ax.pie(counts, labels=counts.index, autopct='%1.0f%%', startangle=90, textprops={'fontsize':13})
            ax.axis('equal')
            st.pyplot(fig)

        # Poem count leaderboard table
        st.markdown("<b>Poem Count Table</b>", unsafe_allow_html=True)
        st.table(counts.reset_index().rename(columns={'index': 'Poet', 'name': 'Poems Submitted'}))

        # Reflection points leaderboard table (next section, after AI reflection!)

    # --- Poem Submission Form ---
    st.markdown("---")
    with st.form(key="poem_form"):
        st.markdown(
            "<div style='margin-bottom:8px; font-size:1.13em; color:#6e5e88;'>Get poet status in the Room – be the brave first line.</div>",
            unsafe_allow_html=True
        )
        name = st.text_input("Your Name")
        poem = st.text_area("Your Poem")
        passkey = st.text_input("Reflective Room Passkey", type="password")
        submit = st.form_submit_button("Submit")

    # --- Submit Logic ---
    reflection_points_this_poem = 0
    posters_to_download = []
    if submit:
        if not name.strip() or not poem.strip():
            st.warning("Please fill in all fields.")
        elif passkey != st.secrets["rr_passkey"]["passkey"]:
            st.error("❌ Incorrect passkey. Please contact your community admin.")
        else:
            worksheet.append_row([name, poem])
            st.success("✅ Poem submitted successfully!")

            # ---- AI Reflection ----
            openai_client = OpenAI(api_key=st.secrets["openai_key"]["openai_key"])
            with st.spinner("🪞 The RR soul is listening..."):
                resp = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a poetry critic. Give a 2-line poetic and honest reflection of this poem. Also, rate it out of 10 as 'Rating: X/10'. Only output the reflection and the rating. Don't add anything else."},
                        {"role": "user", "content": poem}
                    ],
                    max_tokens=70,
                    temperature=0.7
                )
            reflection = resp.choices[0].message.content.strip()

            # --- Extract reflection points (out of 10) ---
            import re
            match = re.search(r'Rating: ?(\d+)/10', reflection)
            if match:
                reflection_points_this_poem = int(match.group(1))
            else:
                reflection_points_this_poem = 0

            st.markdown("---")
            st.markdown("### 🪞 The Reflective Room thinks:")
            st.info(reflection)

            # --- Generate Poetry Posters (handle >11 lines) ---
            poem_lines = [l for l in poem.splitlines() if l.strip()]
            chunk_size = 11
            total_images = (len(poem_lines)-1) // chunk_size + 1
            poster_paths = []
            for i in range(total_images):
                start = i * chunk_size
                end = start + chunk_size
                chunk = "\n".join(poem_lines[start:end])
                poster_path = generate_white_poster_with_logo(name, chunk, img_number=i+1)
                poster_paths.append(poster_path)
                st.image(poster_path, caption=f"✨ Poetry Poster {i+1}", use_column_width=True)
                posters_to_download.append(poster_path)

    # --- Reflection Points Leaderboard ---
    if records:
        df = pd.DataFrame(records)
        if "reflection_points" not in df.columns:
            df["reflection_points"] = 0  # For initial runs

        # Add new reflection points if poem was just submitted
        if submit and reflection_points_this_poem > 0:
            # Reload worksheet with all records, add points to last poem
            ws_vals = worksheet.get_all_values()
            header = ws_vals[0]
            rows = ws_vals[1:]
            if "reflection_points" not in header:
                worksheet.update_cell(1, len(header)+1, "reflection_points")
                header.append("reflection_points")
                for idx, row in enumerate(rows, 2):
                    worksheet.update_cell(idx, len(header), "0")
            worksheet.update_cell(len(ws_vals), len(header), str(reflection_points_this_poem))
            df = pd.DataFrame(worksheet.get_all_records())

        leaderboard = df.groupby("name")["reflection_points"].sum().reset_index().sort_values("reflection_points", ascending=False)
        leaderboard.columns = ["Poet", "Reflection Points"]
        st.markdown(
            "<div style='background:#f6f0e6; border-radius:12px; padding:12px; margin:13px 0 7px 0; box-shadow:0 1px 5px #e7e2fa;'><b>🌟 Reflection Points Leaderboard</b></div>",
            unsafe_allow_html=True)
        st.table(leaderboard)

    # --- Download Posters Button ---
    if posters_to_download:
        with open(posters_to_download[0], "rb") as f:
            btn = st.download_button(
                label=f"Download All Poster{'s' if len(posters_to_download)>1 else ''} (ZIP)",
                data=f.read(),
                file_name="ReflectiveRoom_PoemPoster.png",
                mime="image/png"
            )

except Exception as e:
    st.error(f"❌ Error: {e}")