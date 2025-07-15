import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

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

st.markdown("Share your soul in verse.")

# ---------- Google Sheets Setup ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ---------- Poster Generation Function ----------
def generate_white_poster_with_logo(poet_name: str, poem_text: str) -> str:
    """
    Creates a vertical white-background poster with the poem, poet name, and the Reflective Room logo.
    Returns the file path of the generated poster image.
    """
    img_width, img_height = 1080, 1350
    background_color = "white"
    text_color = "black"

    image = Image.new("RGB", (img_width, img_height), color=background_color)
    draw = ImageDraw.Draw(image)

    # Paste logo
    logo_url = "https://raw.githubusercontent.com/satishmishracode/reflective-room-app/main/The_Reflective_Room_Logo.png"
    try:
        resp = requests.get(logo_url)
        logo = Image.open(BytesIO(resp.content)).convert("RGBA")
        logo = logo.resize((200, int(200 * logo.height / logo.width)))
        logo_x = (img_width - logo.width) // 2
        image.paste(logo, (logo_x, 50), logo)
    except Exception:
        pass

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        poem_font = ImageFont.truetype(font_path, 42)
        name_font = ImageFont.truetype(font_path, 36)
    except Exception:
        poem_font = ImageFont.load_default()
        name_font = ImageFont.load_default()

    margin = 80
    top_text_y = 300
    wrapped = textwrap.fill(poem_text, width=30)

    for line in wrapped.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=poem_font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((img_width - w) / 2, top_text_y), line, font=poem_font, fill=text_color)
        top_text_y += h + 10

    if poet_name:
        name_text = f"— {poet_name}"
        bbox = draw.textbbox((0, 0), name_text, font=name_font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((img_width - w - margin, img_height - h - 60), name_text, font=name_font, fill="gray")

    output_path = "/mnt/data/reflective_room_poem_poster.png"
    image.save(output_path)
    return output_path

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

    # Submission form
    with st.form(key="poem_form"):
        name = st.text_input("Your Name")
        poem = st.text_area("Your Poem")
        submit = st.form_submit_button("Submit")

    if submit:
        if not name.strip() or not poem.strip():
            st.warning("Please fill in both fields.")
        else:
            worksheet.append_row([name, poem])
            st.success("✅ Poem submitted successfully!")

            # AI Reflection
            openai_client = OpenAI(api_key=st.secrets["openai_key"]["openai_key"])
            with st.spinner("🌀 The Reflective Room soul is listening..."):
                resp = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a thoughtful poetry critic. Provide a 2-line honest reflection and rate out of 10."},
                        {"role": "user", "content": poem}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )
            reflection = resp.choices[0].message.content.strip()

            st.markdown("---")
            st.markdown("🔮 **The Reflective Room thinks:**")
            st.info(reflection)

            # Poster
            poster_path = generate_white_poster_with_logo(name, poem)
            st.image(poster_path, caption="✨ Your Poetry Poster", use_column_width=True)

except Exception as e:
    st.error(f"❌ Error: {e}")