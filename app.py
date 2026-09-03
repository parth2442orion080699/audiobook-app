import asyncio
import os
import shutil
from pypdf import PdfReader
import edge_tts
from tqdm.asyncio import tqdm

# ==========================================
# 🌟 SETTINGS
# ==========================================
VOICE = "en-US-AndrewNeural"   # Real human jaisi natural voice
PDF_FILE = "book.pdf"         # PDF file ka naam
OUTPUT_AUDIO = "audiobook.mp3"# Final Audio file ka naam
CHUNK_SIZE = 5                # Har chunk me 5 pages honge
CONCURRENT_WORKERS = 5        # Ek saath 5 chunks parallel process honge (Turbo Speed!)

def extract_chunks_from_pdf(pdf_path, chunk_size):
    print(f"📖 Reading '{pdf_path}'...")
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"📄 Total Pages Found: {total_pages}")
    
    chunks = []
    current_text = ""
    current_idx = 1
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            current_text += text + "\n"
        
        # Har chunk_size par ya aakhri page par chunk save karna
        if (i + 1) % chunk_size == 0 or (i + 1) == total_pages:
            if current_text.strip():
                chunks.append((current_idx, current_text.strip()))
                current_idx += 1
            current_text = ""
            
    return chunks, total_pages

async def process_chunk(chunk_idx, text, temp_folder, semaphore, pbar):
    temp_file = os.path.join(temp_folder, f"part_{chunk_idx:04d}.mp3")
    async with semaphore:
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(temp_file)
        except Exception as e:
            print(f"\n⚠️ Part {chunk_idx} me error aaya: {e}")
        finally:
            pbar.update(1)
    return temp_file

async def main():
    if not os.path.exists(PDF_FILE):
        print(f"❌ Error: '{PDF_FILE}' file nahi mili! Folder me 'book.pdf' rakhein.")
        return

    # Purani temporary files saaf karna
    temp_dir = "temp_audio_parts"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    # Chunks extract karna
    chunks, total_pages = extract_chunks_from_pdf(PDF_FILE, CHUNK_SIZE)
    total_chunks = len(chunks)
    
    if total_chunks == 0:
        print("❌ Error: PDF me se text nahi nikal paya!")
        return

    print(f"⚡ Book ko {total_chunks} parts me divide kiya gaya hai.")
    print(f"🚀 JARVIS Turbo Engine: Ek saath {CONCURRENT_WORKERS} parts download ho rahe hain...\n")

    semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)
    
    # 📊 Live Progress Bar
    pbar = tqdm(total=total_chunks, desc="🎙️ Converting Audiobook", unit="part")

    tasks = [
        process_chunk(idx, text, temp_dir, semaphore, pbar)
        for idx, text in chunks
    ]
    
    temp_files = await asyncio.gather(*tasks)
    pbar.close()

    print("\n🔄 Sabhi parts ko ek single MP3 file me combine kiya ja raha hai...")
    temp_files.sort()
    
    with open(OUTPUT_AUDIO, "wb") as outfile:
        for tf in temp_files:
            if os.path.exists(tf):
                with open(tf, "rb") as infile:
                    outfile.write(infile.read())

    # Temporary folder delete karna
    shutil.rmtree(temp_dir)
    
    print(f"\n🎉 BOOM! Mubarak ho Young Boss! Turbo Audiobook ready: '{OUTPUT_AUDIO}' 🎧🔥")

if __name__ == "__main__":
    asyncio.run(main())
