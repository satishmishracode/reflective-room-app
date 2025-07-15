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
import os
import re

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
def generate_white_poster_with_logo(poet_name: str, poem_text: str, img_number=1, poem_title: str = "", instagram_handle: str = "") -> str:
    img_width, img_height = 1080, 1080
    background_color = "white"
    text_color = "black"

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
        title_font = ImageFont.truetype(font_bold_path, 38)
        ig_font = ImageFont.truetype(font_path, 32)
    except Exception:
        poem_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        ig_font = ImageFont.load_default()

    margin = 90
    top_text_y = 260

    # Draw Poem Title (if present)
    if poem_title.strip():
        title_text = poem_title.strip()
        w, h = draw.textbbox((0, 0), title_text, font=title_font)[2:]
        draw.text(((img_width - w) / 2, top_text_y - 80), title_text, font=title_font, fill="#554488")
        top_text_y += 10

    # Wrap and draw poem text (centered)
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

    # Draw Instagram handle at bottom left
    if instagram_handle.strip():
        ig_text = instagram_handle.strip()
        w, h = draw.textbbox((0, 0), ig_text, font=ig_font)[2:]
        draw.text((margin, img_height - h - 65), ig_text, font=ig_font, fill="#b795eb")

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

    # Display stats
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

    # --- Poem Submission Form ---
    st.markdown("---")
    with st.form(key="poem_form"):
        st.markdown(
            "<div style='margin-bottom:8px; font-size:1.13em; color:#6e5e88;'>Get poet status in the Room – be the brave first line.</div>",
            unsafe_allow_html=True
        )
        name = st.text_input("Your Name")
        poem_title = st.text_input("Poem Title (optional)")
        poem = st.text_area("Your Poem")
        instagram_handle = st.text_input("Instagram Handle (optional)", placeholder="@yourhandle")
        passkey = st.text_input("Reflective Room Passkey", type="password")
        submit = st.form_submit_button("Submit")

    reflection_points_this_poem = 0
    posters_to_download = []
    if submit:
        if not name.strip() or not poem.strip():
            st.warning("Please fill in all fields.")
        elif passkey != st.secrets["community_passkey"]["passkey"]:
            st.error("❌ Incorrect passkey. Please contact your community admin.")
        else:
            # Add row with blanks for reflection_points (to be updated after reflection)
            worksheet.append_row([name, poem, '', poem_title, instagram_handle])
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
                poster_path = generate_white_poster_with_logo(
                    name, chunk, img_number=i+1,
                    poem_title=poem_title if i == 0 else "",
                    instagram_handle=instagram_handle if i == (total_images-1) else ""
                )
                poster_paths.append(poster_path)
                st.image(poster_path, caption=f"✨ Poetry Poster {i+1}", use_column_width=True)
                posters_to_download.append(poster_path)

            # Update reflection points for this poem (in the sheet, last submitted row)
            ws_vals = worksheet.get_all_values()
            header = ws_vals[0]
            rows = ws_vals[1:]
            col_idx = header.index("reflection_points") + 1 if "reflection_points" in header else len(header) + 1
            worksheet.update_cell(len(ws_vals), col_idx, str(reflection_points_this_poem))

    # --- Reflection Points Leaderboard ---
    if records:
        df = pd.DataFrame(records)
        if "reflection_points" not in df.columns:
            df["reflection_points"] = 0

        # Add new reflection points if poem was just submitted
        if submit and reflection_points_this_poem > 0:
            ws_vals = worksheet.get_all_values()
            header = ws_vals[0]
            df = pd.DataFrame(worksheet.get_all_records())

        leaderboard = df.groupby("name")["reflection_points"].sum().reset_index().sort_values("reflection_points", ascending=False)
        leaderboard.columns = ["Poet", "Reflection Points"]
        st.markdown(
            "<div style='background:#f6f0e6; border-radius:12px; padding:12px; margin:13px 0 7px 0; box-shadow:0 1px 5px #e7e2fa;'><b>🌟 Reflection Points Leaderboard</b></div>",
            unsafe_allow_html=True)
        st.table(leaderboard)

    # --- Download Posters Button ---
    if posters_to_download:
        import zipfile
        from io import BytesIO
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for idx, path in enumerate(posters_to_download):
                zipf.write(path, os.path.basename(path))
        zip_buffer.seek(0)
        st.download_button(
            label=f"Download All Poster{'s' if len(posters_to_download)>1 else ''} (ZIP)",
            data=zip_buffer,
            file_name="ReflectiveRoom_PoemPosters.zip",
            mime="application/zip"
        )

except Exception as e:
    st.error(f"❌ Error: {e}")