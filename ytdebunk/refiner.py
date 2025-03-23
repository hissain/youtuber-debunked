import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

def chunk_text(text, max_chars=3000):
    sentences = text.split("।")
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + "।"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "।"

    if current_chunk:  
        chunks.append(current_chunk.strip())

    return chunks

enchacement_prompt = """
You are a Bangla language expert. You have been asked to improve the following Bangla transcription by correcting errors and enhancing readability.

IMPORTANT:
1. Return only the transcription without any additional information or instructions.
2. Do not change the meaning of the transcription.
3. Do not add any new information to the transcription.
4. Do not remove any information from the transcription.

Here is the transcription:

"""

def enhance_transcription(transcription, key=os.getenv("GENAI_API_KEY")):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    chunks = chunk_text(transcription)
    refined_chunks = []

    for chunk in chunks:
        print("Refining chunk no. ", chunks.index(chunk) + 1)
        prompt = enchacement_prompt + chunk
        response = model.generate_content(prompt)
        refined_chunks.append(response.text.strip())
    return " ".join(refined_chunks)


if __name__ == "__main__":
    transcription = "কম্পিউটারে বাংলা লেখার অনেক গুলো পদ্ধতি আছে। সাধারণত বাংলা লেখার জন্য কম্পিইটারে কিছু সফ্টওয়ার যেমন অভ্র, বিজয় ইত্যাদি ইনস্টল করতে হয়।এসব সফ্টওয়ারে  ব্যবহার করে সহজেই বাংলা টাইপ করা যায়। সফ্টওয়ার ইনস্টল করা ছাড়াও ইন্টারনেট ব্যবহার করে বিভিন্ন ওয়েবসাইটে বাংলা লেখা সম্ভব। সফ্টওয়ার ইনস্টল ছাড়া বাংলা লেখা যায়।"
    refined_transcription = enhance_transcription(transcription)
    print(f"Refined transcription:\n{refined_transcription}")