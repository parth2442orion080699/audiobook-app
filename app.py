import streamlit as st
import asyncio
import os
import re
import shutil
import tempfile
from pypdf import PdfReader
import edge_tts
import nest_asyncio

# Asyncio loop fix for Streamlit
nest_asyncio.apply()

st.set_page_config(page_title="JARVIS Turbo Audiobook", page_icon="⚡", layout="centered")

st.title("⚡ JARVIS Turbo Audiobook Generator")
st.markdown("Apni PDF book upload kijiye aur **Super-Fast Parallel Speed** me Audiobook paaiye!")

# 🎙️ Voice Selection
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

uploaded_file = st.file_uploader("📁 PDF Book Upload Karein", type=["pdf"])

def extract_clean_chunks(pdf_file, chunk_size=5):
    reader = PdfReader(pdf_file)
    total_pages = len(reader.pages)
    
    chunks = []
    current_text = ""
    current_idx = 1
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            cleaned = re.sub(r'\s+', ' ', text).strip()
            if cleaned:
                current_text += cleaned + "\n"
        
        if (i + 1) % chunk_size == 0 or (i + 1) == total_pages:
            if current_text.strip():
                chunks.append((current_idx, current_text.strip()))
                current_idx += 1
            current_text = ""
            
    return chunks, total_pages

async def process_single_chunk(chunk_idx, text, temp_folder, voice, semaphore, progress_callback):
    temp_file = os.path.join(temp_folder, f"part_{chunk_idx:04d}.mp3")
    async with semaphore:
        if text.strip():
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_file)
            except Exception:
                pass
        progress_callback()
    return temp_file

async def run_turbo_pipeline(chunks, voice, temp_dir, progress_bar):
    total_chunks = len(chunks)
    completed = 0
    
    def on_chunk_done():
        nonlocal completed
        completed += 1
        pct = int((completed / total_chunks) * 100)
        progress_bar.progress(pct, text=f"⚡ Turbo Speed: {completed}/{total_chunks} parts done ({pct}%)")

    semaphore = asyncio.Semaphore(5) # 5 parallel workers
    tasks = [
        process_single_chunk(idx, text, temp_dir, voice, semaphore, on_chunk_done)
        for idx, text in chunks
    ]
    temp_files = await asyncio.gather(*tasks)
    return temp_files

if uploaded_file is not None:
    if st.button("🚀 Generate Turbo Audiobook", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="📖 PDF book scan ho rahi hai...")
        temp_dir = tempfile.mkdtemp()
        
        try:
            chunks, total_pages = extract_clean_chunks(uploaded_file, chunk_size=5)
            total_chunks = len(chunks)
            
            if total_chunks == 0:
                st.error("❌ Is PDF me se text nahi mil paya! Kripya text-based PDF use karein.")
            else:
                st.info(f"📄 Total Pages: {total_pages} | ⚡ Divide kiya: {total_chunks} Parts me")
                
                # Run Parallel Pipeline
                temp_files = asyncio.run(run_turbo_pipeline(chunks, selected_voice, temp_dir, progress_bar))
                
                progress_bar.progress(100, text="🔄 Sabhi parts ko merge kiya ja raha hai...")
                
                # Merge into single MP3
                temp_files.sort()
                output_mp3_path = os.path.join(temp_dir, "final_audiobook.mp3")
                with open(output_mp3_path, "wb") as outfile:
                    for tf in temp_files:
                        if os.path.exists(tf):
                            with open(tf, "rb") as infile:
                                outfile.write(infile.read())

                progress_bar.progress(100, text="🎉 Audiobook Successfully Ban Gayi!")
                st.success(f"✅ Total {total_pages} Pages ki Audiobook taiyar hai!")
                
                # Audio Player & Download
                with open(output_mp3_path, "rb") as f:
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
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
