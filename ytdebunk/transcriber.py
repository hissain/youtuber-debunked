import librosa
import torch
import torchaudio
import numpy as np
import ytdebunk.settings as settings
from transformers import WhisperTokenizer, WhisperProcessor, WhisperFeatureExtractor, WhisperForConditionalGeneration
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")

chunk_duration = 30  # Seconds per chunk
sampling_rate_target = 16000

def load_model(model_path, device):
    print("[ytdebunk-transcriber] Loading WhisperFeatureExtractor model...")
    feature_extractor = WhisperFeatureExtractor.from_pretrained(model_path)
    tokenizer = WhisperTokenizer.from_pretrained(model_path)
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
    return feature_extractor, tokenizer, processor, model

def transcribe_audio(
        audio_path=settings.AUDIO_FILE, 
        start_time=None, 
        end_time=None,
        model_path=settings.TRANSCRIPTION_MODEL,
        verbose=False):
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    feature_extractor, tokenizer, processor, model = load_model(model_path, device)
    
    speech_array, sampling_rate = torchaudio.load(audio_path)
    speech_array = speech_array[0].numpy()
    speech_array = librosa.resample(speech_array, orig_sr=sampling_rate, target_sr=sampling_rate_target)
    
    start_sample = int((start_time or 0) * sampling_rate_target)
    end_sample = int(end_time * sampling_rate_target) if end_time is not None else len(speech_array)
    speech_array = speech_array[start_sample:end_sample]
    
    chunk_size = chunk_duration * sampling_rate_target
    num_chunks = int(np.ceil(len(speech_array) / chunk_size))

    transcriptions = []

    print(f"[ytdebunk-transcriber] Transcribing {num_chunks} chunks...")
    for i in range(num_chunks):
        if verbose:
            print(f"[ytdebunk-transcriber] Transcribing chunk {i + 1} of {num_chunks}...")
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(speech_array))
        
        chunk = speech_array[start:end]
        input_features = feature_extractor(chunk, sampling_rate=sampling_rate_target, return_tensors="pt").input_features.to(device)

        predicted_ids = model.generate(input_features)[0]
        transcription = processor.decode(predicted_ids, skip_special_tokens=True)
        transcriptions.append(transcription)

    full_transcription = " ".join(transcriptions)

    if verbose:
        print(f"[ytdebunk-transcriber] Transcription complete!")

    return full_transcription
