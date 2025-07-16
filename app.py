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
import re

st.set_page_config(page_title="The Reflective Room", layout="centered")

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

# ======== GOOGLE SHEETS SECTION ========
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

def extract_score(reflection: str):
    match = re.search(r"(\d+)/10", reflection)
    if match:
        try:
            return int(match.group(1))
        except Exception:
            return 0
    return 0

# ========= GEMINI MODEL PICKER ==========
def gemini_model_picker():
    """
    Returns the best available generative text model from Gemini API, preferring new, supported models.
    """
    import google.generativeai as genai
    try:
        preferred = [
            "gemini-1.5-flash",
            "models/gemini-1.5-flash",
            "gemini-1.5-pro",
            "models/gemini-1.5-pro"
        ]
        models = genai.list_models()
        model_names = [m.name for m in models if "generateContent" in getattr(m, "supported_generation_methods", [])]

        for model in preferred:
            if model in model_names:
                return model
        for m in model_names:
            if all(x not in m for x in ["vision", "bison", "pro-vision", "1.0"]):
                return m
        if model_names:
            return model_names[0]
    except Exception:
        pass
    return None

st.markdown(" ", unsafe_allow_html=True)  # Spacer

# ============ POETRY SUBMISSION + GOOGLE SHEETS ============
try:
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
                openai_client = OpenAI(api_key=st.secrets["openai_key"]["openai_key"])
                with st.spinner("The Reflective Room is listening..."):
                    ai_resp = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are Apollo, a Greek god of poetry and wisdom in the 21st century, who references classic English poets. Offer a 2-3 line poetic critique and a score out of 10 for this poem."},
                            {"role": "user", "content": poem}
                        ],
                        max_tokens=80,
                        temperature=0.7
                    )
                reflection_ai = ai_resp.choices[0].message.content.strip()
                reflection_score = extract_score(reflection_ai)
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

    # Pie Chart of Poem Counts ("Constellation of Voices")
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

    # AI Reflection (only after submission)
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

except Exception as e:
    st.error(f"⚠️ Google Sheets features unavailable: {e}")

# ========= 🎧 AUDIO GENERATION FEATURE (ALWAYS VISIBLE) ==========
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

# =============== Apollo & Lyra Council (OpenAI + Gemini) ===============
with st.expander("🌞🌙 Whispers of Apollo & Lyra (Poetic Council)"):
    st.markdown("Experience a poetic dialogue between Apollo (structure, reason) and Lyra (lyric, intuition) as they reflect on your poem and offer a divine score.")

    if st.session_state.get("submission_successful", False):
        submitted_poem = st.session_state["submission_data"].get("poem", "")
        poet_name = st.session_state["submission_data"].get("name", "")
        apollo_text_1 = st.session_state.get("reflection_ai", "")

        # 1. Lyra (Gemini) responds dynamically!
        try:
            import google.generativeai as genai
            genai.configure(api_key=st.secrets["gemini"]["api_key"])
            lyra_model_name = gemini_model_picker()
            if not lyra_model_name:
                raise Exception("No compatible Gemini model found for your API key.")

            lyra_model = genai.GenerativeModel(lyra_model_name)
            lyra_prompt_1 = (
                f"You are Lyra, a witty, intuitive Greek muse of poetry in the 21st century. "
                f"Apollo (the god of poetry) just reflected on this poem by {poet_name}:\n"
                f"---\nPOEM:\n{submitted_poem}\n---\n"
                f"APOLLO'S REFLECTION:\n{apollo_text_1}\n---\n"
                "Now, in 2-3 lines, provide your own lyrical reflection, tease Apollo, reference an English poet if you wish, give your own score out of 10 (different from Apollo's if you wish), and address the poet by name. Invite Apollo for a closing banter."
            )
            lyra_resp_1 = lyra_model.generate_content(lyra_prompt_1)
            lyra_text_1 = lyra_resp_1.text.strip()
            used_model = lyra_model_name
        except Exception as e:
            lyra_text_1 = f"⚠️ Lyra could not generate a response: {e}"
            used_model = None

        # Extract scores and compute divine score
        def extract_score(text):
            match = re.search(r"(\d+)/10", text)
            if match:
                try:
                    return int(match.group(1))
                except Exception:
                    return None
            return None

        apollo_score = extract_score(apollo_text_1)
        lyra_score = extract_score(lyra_text_1)
        scores = [s for s in [apollo_score, lyra_score] if s is not None]
        divine_score = round(sum(scores) / len(scores), 1) if scores else "N/A"

        st.markdown("---")
        st.markdown("**🌞 Apollo says:**")
        st.info(apollo_text_1)
        st.markdown("**🌙 Lyra replies:**")
        st.info(lyra_text_1)
        if used_model:
            st.caption(f"Lyra used Gemini model: `{used_model}`")
        st.markdown(f"**✨ Divine Score:** `{divine_score} / 10`")
    else:
        st.info("Please submit a poem to experience Apollo & Lyra's poetic council.")

st.markdown("---")
st.caption("Crafted with ❤️ for poets, writers, and seekers.")