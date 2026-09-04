import streamlit as st
import asyncio
import os
import re
import shutil
import tempfile
import threading
from pypdf import PdfReader
import edge_tts

st.set_page_config(page_title="JARVIS Turbo Audiobook", page_icon="⚡", layout="centered")

st.title("⚡ JARVIS Turbo Audiobook Generator")
st.markdown("Apni PDF book upload kijiye aur **100% Free High-Quality Audiobook** paaiye!")

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

async def process_single_chunk(chunk_idx, text, temp_folder, voice, semaphore):
    temp_file = os.path.join(temp_folder, f"part_{chunk_idx:04d}.mp3")
    async with semaphore:
        if text.strip():
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_file)
            except Exception:
                pass
    return temp_file

async def run_parallel_tts(chunks, voice, temp_dir):
    semaphore = asyncio.Semaphore(5)  # 5 parallel tasks (Super Fast)
    tasks = [
        process_single_chunk(idx, text, temp_dir, voice, semaphore)
        for idx, text in chunks
    ]
    return await asyncio.gather(*tasks)

# 🛡️ Safe Isolated Thread Runner (Zero Crash Guarantee)
def run_safe_async(coro):
    res = []
    err = []
    def target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res.append(loop.run_until_complete(coro))
        except Exception as e:
            err.append(e)
        finally:
            loop.close()
    t = threading.Thread(target=target)
    t.start()
    t.join()
    if err:
        raise err[0]
    return res[0]

if uploaded_file is not None:
    if st.button("🚀 Generate Turbo Audiobook", type="primary", use_container_width=True):
        progress_bar = st.progress(10, text="📖 PDF book scan ho rahi hai...")
        temp_dir = tempfile.mkdtemp()
        
        try:
            chunks, total_pages = extract_clean_chunks(uploaded_file, chunk_size=5)
            total_chunks = len(chunks)
            
            if total_chunks == 0:
                st.error("❌ Is PDF me se text nahi mil paya! Kripya text-based PDF use karein.")
            else:
                st.info(f"📄 Total Pages: {total_pages} | ⚡ Divide kiya: {total_chunks} Parts me")
                progress_bar.progress(35, text=f"⚡ Turbo Parallel Engine: {total_chunks} parts convert ho rahe hain...")
                
                # Run parallel download in isolated safe thread
                temp_files = run_safe_async(run_parallel_tts(chunks, selected_voice, temp_dir))
                
                progress_bar.progress(85, text="🔄 Sabhi parts ko MP3 me merge kiya ja raha hai...")
                
                # Merge into single MP3
                temp_files.sort()
                output_mp3_path = os.path.join(temp_dir, "final_audiobook.mp3")
                with open(output_mp3_path, "wb") as outfile:
                    for tf in temp_files:
                        if os.path.exists(tf):
                            with open(tf, "rb") as infile:
                                outfile.write(infile.read())

                progress_bar.progress(100, text="🎉 Audiobook successfully ready!")
                st.success(f"✅ Total {total_pages} Pages ki Audiobook taiyar hai!")
                
                # Audio Player & Download Button
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
