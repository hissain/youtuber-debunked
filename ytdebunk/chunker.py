import re
from typing import List

def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    """
    Split text into chunks of at most max_chars, respecting natural sentence
    boundaries for both Bengali (danda '।'), Latin/English ('.', '!', '?'), and newlines.
    
    If an individual sentence exceeds max_chars, it will be split on whitespace
    boundaries to prevent truncation or excessive payload sizes.
    """
    if not text:
        return []

    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Split on sentence boundary punctuation: Bengali danda (।), period (.), !, ?, or newline
    # Using positive lookbehind to retain the punctuation with each sentence
    sentences = re.split(r'(?<=[।\.!\?\n])\s+', text)

    # Fallback if no sentence boundaries exist in a very long text: split by words
    if len(sentences) == 1 and len(sentences[0]) > max_chars:
        words = sentences[0].split()
        chunks = []
        curr = ""
        for w in words:
            if len(curr) + len(w) + 1 <= max_chars:
                curr = f"{curr} {w}" if curr else w
            else:
                if curr:
                    chunks.append(curr)
                # If a single word is larger than max_chars, slice it hard
                while len(w) > max_chars:
                    chunks.append(w[:max_chars])
                    w = w[max_chars:]
                curr = w
        if curr:
            chunks.append(curr)
        return chunks

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If a single sentence exceeds max_chars, recurse to split it safely
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            sub_chunks = chunk_text(sentence, max_chars=max_chars)
            if sub_chunks:
                chunks.extend(sub_chunks[:-1])
                current_chunk = sub_chunks[-1]
            continue

        if current_chunk:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += " " + sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
        else:
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
