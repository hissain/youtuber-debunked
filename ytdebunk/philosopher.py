import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

def chunk_text(text, max_chars=3000):
    sentences = text.split("।")
    chunks, current_chunk = [], ""

    for sentence in sentences:
        # Prevent chunks from exceeding max_chars, even if they don't end with "।"
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + "।"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + "।"

    # Append last chunk if any remains
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

enhancement_prompt = """
You are a Bangla language expert and a philosopher specializing in detecting logical flows, fallacies, bias, and irony in a Bangla speaker's content. Please be precise and critical while evaluating a piece of Bangla content from a Bangla-speaking YouTuber.

IMPORTANT:
1. Generate in Bangla only.
2. Keep the fallacy, bias, irony, and logical faults in the same order as they appear in the content.
3. Keep the summary concise and to the point and withing single large paragraph without showing point by point.

Here is the speaker's text:
"""

def detect_logical_faults(transcription, key=os.getenv("GENAI_API_KEY")):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    chunks = chunk_text(transcription)
    refined_chunks = []

    for idx, chunk in enumerate(chunks):
        print(f"Refining chunk {idx + 1} of {len(chunks)}")
        prompt = enhancement_prompt + chunk
        try:
            response = model.generate_content(prompt)
            refined_chunks.append(response.text.strip())
        except Exception as e:
            print(f"Error while processing chunk {idx + 1}: {e}")
            refined_chunks.append(f"Error processing chunk {idx + 1}")

    return " ".join(refined_chunks)


if __name__ == "__main__":
    transcription = "বেমস্টেকের শীর্ষ সম্মেলনের ফাঁকে প্রধান উপদেষ্টা ডক্টর মুম্বাদী ইনুসের সাথে ভারতের প্রধানমন্ত্রী নরেন্দ্র মোদীর সঙ্গে বৈঠক করে কূটনৈতিক পত্র দিয়েছে বাংলাদেশ। চার দিনের পারস্পরিক প্রতিনিধি প্রত্যেক প্রাষ্ট্রের উপদেষ্টা তহিদ সেন। ক্ষোভান্বিত নীতি নির্ধারক বার্তা দেখে তবে ভারতের পররাষ্ট্রমন্ত্রী এস জয়শঙ্কর নয়াদিল্লীতে সংশোধনী প্যানেলের একটি বৈঠকে তথ্য দিয়েছেন সেটি আবার ভিন্ন বার্তা দেখাচ্ছে। জয়শঙ্কর কোনো চুক্তি স্বাক্ষরিত  এটমিক  কেশীয় মেমোর‍্যান্ডাম হতে পরিত্রাণ প্রতিজ্ঞাবদ্ধ মত দূরীভূত।ই মুহূর্তে আশ্বাস নাই আসলে।"
    refined_transcription = detect_logical_faults(transcription)
    print(f"Fallacies:\n{refined_transcription}")
