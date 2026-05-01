import os
import time
import glob
from google import genai
from google.genai import types

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEGMENTS_DIR = os.path.join(BASE_DIR, "projects/dozle_kirinuki/work/highlight_rDYmTp/output/diarize_tmp/segments")
OUTPUT_FILE = os.path.join(BASE_DIR, "projects/dozle_kirinuki/work/highlight_rDYmTp/output/gemini_diarize_named.srt")

# Vertex AI ADC client
client = genai.Client(vertexai=True, project="gen-lang-client-0119911773", location="global")

def transcribe_segment(file_path, segment_index):
    print(f"Uploading segment: {file_path}...")
    sample_file = client.files.upload(
        file=file_path,
        config=types.UploadFileConfig(display_name=f"Segment {segment_index}"),
    )

    while sample_file.state.name == "PROCESSING":
        time.sleep(5)
        sample_file = client.files.get(name=sample_file.name)

    offset_sec = segment_index * 300
    prompt = (
        f"この音声は、動画全体の {offset_sec}秒から始まる部分です。この音声を聴いて、SRT形式で文字起こしをしてください。\n"
        "ルール：\n"
        "1. 話者を識別し、[名前]形式（例: [ドズル], [ぼんじゅうる], [おんりー], [おらふくん], [メニー]）で含めること。\n"
        "2. タイムスタンプは HH:MM:SS,mmm 形式（ミリ秒精度）にし、全体の開始時間に合わせてオフセットを必ず加算してください。\n"
        f"   (例: 音声内での 00:00:10 は、SRT上では {offset_sec + 10}秒に対応する時間にすること)\n"
        "3. 全て日本語で、文脈から話し手を特定して書き出してください。"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, sample_file],
    )
    client.files.delete(name=sample_file.name)
    return response.text

def main():
    segment_files = sorted(glob.glob(os.path.join(SEGMENTS_DIR, "seg_*.wav")))
    full_srt = ""

    for i, file_path in enumerate(segment_files):
        print(f"Processing segment {i+1}/{len(segment_files)}...")
        try:
            segment_srt = transcribe_segment(file_path, i)
            full_srt += segment_srt + "\n\n"
        except Exception as e:
            print(f"Error in segment {i}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_srt)

    print(f"All segments processed. Result saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
