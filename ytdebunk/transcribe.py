import os
import argparse
import librosa
import torch
import torchaudio
import numpy as np
from transformers import WhisperTokenizer, WhisperProcessor, WhisperFeatureExtractor, WhisperForConditionalGeneration

chunk_duration = 30  # Seconds per chunk
sampling_rate_target = 16000

def load_model(model_path, device):
    feature_extractor = WhisperFeatureExtractor.from_pretrained(model_path)
    tokenizer = WhisperTokenizer.from_pretrained(model_path)
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
    return feature_extractor, tokenizer, processor, model

def transcribe_audio(audio_path="downloads/audio.mp3", start_time=0.0, end_time=None, output_file="downloads/transcription.txt", model_path="bangla-speech-processing/BanglaASR"):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    feature_extractor, tokenizer, processor, model = load_model(model_path, device)
    
    speech_array, sampling_rate = torchaudio.load(audio_path)
    speech_array = speech_array[0].numpy()
    speech_array = librosa.resample(speech_array, orig_sr=sampling_rate, target_sr=sampling_rate_target)
    
    start_sample = int(start_time * sampling_rate_target)
    end_sample = int(end_time * sampling_rate_target) if end_time is not None else len(speech_array)
    speech_array = speech_array[start_sample:end_sample]
    
    chunk_size = chunk_duration * sampling_rate_target  # Number of samples per chunk
    num_chunks = int(np.ceil(len(speech_array) / chunk_size))

    transcriptions = []

    for i in range(num_chunks):
        print(f"Processing chunk {i + 1} of {num_chunks}...")
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(speech_array))
        
        chunk = speech_array[start:end]
        input_features = feature_extractor(chunk, sampling_rate=sampling_rate_target, return_tensors="pt").input_features.to(device)

        predicted_ids = model.generate(input_features)[0]
        transcription = processor.decode(predicted_ids, skip_special_tokens=True)
        transcriptions.append(transcription)

    full_transcription = " ".join(transcriptions)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_transcription)
    
    print("Transcription saved to", output_file)
    print(full_transcription)
