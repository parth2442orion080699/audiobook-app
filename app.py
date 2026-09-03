import streamlit as st
import asyncio
import os
import re
from pypdf import PdfReader
import edge_tts

# 🌟 Page Configuration (Mobile Friendly Look)
st.set_page_config(page_title="JARVIS Audiobook Generator", page_icon="🎧", layout="centered")

st.title("🎧 JARVIS Audiobook Generator")
st.markdown("Apni manpasand **PDF Book** upload kijiye aur 100% Free High-Quality **Audiobook** paaiye!")

# 🎙️ Voice Selection Dropdown
voice_choice = st.selectbox(
    "🎙️ Select Voice (Aawaz choose karein):",
    [
        "Andrew (Male - Natural Storyteller)",
        "Aria (Female - Natural Voice)",
        "Guy (Male - Deep Voice)",
        "Jenny (Female - Clear Voice)"
    ]
)

voice_map = {
    "Andrew (Male - Natural Storyteller)": "en-US-AndrewNeural",
    "Aria (Female - Natural Voice)": "en-US-AriaNeural",
    "Guy (Male - Deep Voice)": "en-US-GuyNeural",
    "Jenny (Female - Clear Voice)": "en-US-JennyNeural"
}
selected_voice = voice_map[voice_choice]

# 📁 File Uploader
uploaded_file = st.file_uploader("📁 PDF Book Upload Karein", type=["pdf"])

async def generate_tts(text, voice, out_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_file)

if uploaded_file is not None:
    if st.button("🚀 Generate Audiobook", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="📖 PDF book scan ho rahi hai...")
        
        try:
            reader = PdfReader(uploaded_file)
            total_pages = len(reader.pages)
            
            full_text = ""
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    cleaned = re.sub(r'\s+', ' ', text).strip()
                    if cleaned:
                        full_text += cleaned + "\n"
                
                pct = int(((i + 1) / total_pages) * 40)
                progress_bar.progress(pct, text=f"📄 Page {i+1}/{total_pages} read kiya...")

            if not full_text.strip():
                st.error("❌ Is PDF me se text nahi mil paya! Kripya text-based PDF use karein.")
            else:
                progress_bar.progress(50, text="🎙️ JARVIS Voice Engine audio bana raha hai (Please wait)...")
                
                output_filename = "final_audiobook.mp3"
                asyncio.run(generate_tts(full_text, selected_voice, output_filename))
                
                progress_bar.progress(100, text="🎉 Audiobook successfully ban gayi!")
                st.success(f"✅ Total {total_pages} Pages ki Audiobook taiyar hai!")
                
                # 🎵 Audio Player & Download Button
                with open(output_filename, "rb") as f:
                    audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    clean_name = uploaded_file.name.rsplit('.', 1)[0]
                    st.download_button(
                        label="⬇️ Download MP3 Audiobook",
                        data=audio_bytes,
                        file_name=f"{clean_name}_Audiobook.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
        except Exception as e:
            st.error(f"⚠️ Error aaya: {e}")
