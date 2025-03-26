import librosa
import torch
import torchaudio
import numpy as np
import bisect
import ytdebunk.settings as settings
from transformers import WhisperTokenizer, WhisperProcessor, WhisperFeatureExtractor, WhisperForConditionalGeneration
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")

chunk_duration = 14
sampling_rate_target = 16000
silence_window = 0.5

def load_model(model_path, device):
    print("[ytdebunk-transcriber] Loading Whisper model components...")
    feature_extractor = WhisperFeatureExtractor.from_pretrained(model_path)
    tokenizer = WhisperTokenizer.from_pretrained(model_path)
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
    return feature_extractor, tokenizer, processor, model

def detect_silent_intervals(speech_array, sr):
    frame_length = 2048
    hop_length = 512
    rms = librosa.feature.rms(y=speech_array, frame_length=frame_length, hop_length=hop_length)
    rms_values = rms[0]
    
    # Dynamic threshold based on 10th percentile of RMS values
    threshold = np.percentile(rms_values, 10)
    silent = rms_values < threshold
    
    # Calculate frame times
    n_frames = len(rms_values)
    frame_start_times = (np.arange(n_frames) * hop_length) / sr
    frame_end_times = frame_start_times + (frame_length / sr)
    
    # Find silent intervals
    diff = np.diff(silent.astype(int))
    starts = np.where(diff == 1)[0] + 1
    ends = np.where(diff == -1)[0] + 1
    
    if silent[0]:
        starts = np.insert(starts, 0, 0)
    if silent[-1]:
        ends = np.append(ends, len(silent))
    
    silent_intervals = []
    for s, e in zip(starts, ends):
        start_time = frame_start_times[s]
        end_time = frame_end_times[e-1] if e > 0 else frame_end_times[e]
        silent_intervals.append((start_time, end_time))
    
    return silent_intervals

def generate_split_points(silent_intervals, total_duration):
    split_candidates = []
    for start, end in silent_intervals:
        split_candidates.extend([start, end])
    split_candidates = sorted(split_candidates)
    
    split_points = [0.0]
    current_start = 0.0
    
    while current_start < total_duration:
        target_time = current_start + chunk_duration
        left = target_time - silence_window
        right = target_time + silence_window
        
        # Find nearest split candidate in window
        left_idx = bisect.bisect_left(split_candidates, left)
        right_idx = bisect.bisect_right(split_candidates, right)
        candidates = split_candidates[left_idx:right_idx]
        
        if candidates:
            split_time = min(candidates, key=lambda x: abs(x - target_time))
        else:
            split_time = target_time
        
        split_time = min(split_time, total_duration)
        if split_time > split_points[-1]:
            split_points.append(split_time)
        current_start = split_time
    
    if split_points[-1] < total_duration:
        split_points.append(total_duration)
    
    return split_points

def transcribe_audio(
        audio_path=settings.AUDIO_FILE, 
        start_time=None, 
        end_time=None,
        verbose=False,
        language=settings.LANUAGE_DEFAULT):
    
    model_path = settings.TRANSCRIPTION_MODELS[language]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    feature_extractor, tokenizer, processor, model = load_model(model_path, device)
    
    # Load and process audio
    speech_array, sampling_rate = torchaudio.load(audio_path)
    speech_array = speech_array[0].numpy()
    speech_array = librosa.resample(speech_array, orig_sr=sampling_rate, target_sr=sampling_rate_target)
    
    # Apply time bounds
    start_sample = int((start_time or 0) * sampling_rate_target)
    end_sample = int(end_time * sampling_rate_target) if end_time else len(speech_array)
    speech_array = speech_array[start_sample:end_sample]
    total_duration = len(speech_array) / sampling_rate_target
    
    # Detect silent intervals and generate split points
    silent_intervals = detect_silent_intervals(speech_array, sampling_rate_target)
    split_points = generate_split_points(silent_intervals, total_duration)
    
    transcriptions = []
    print(f"[ytdebunk-transcriber] Transcribing {len(split_points)-1} chunks...")
    
    for i in range(len(split_points) - 1):
        if verbose:
            print(f"[ytdebunk-transcriber] Processing chunk {i+1}/{len(split_points)-1} ({split_points[i]:.1f}s - {split_points[i+1]:.1f}s)")
        
        start = int(split_points[i] * sampling_rate_target)
        end = int(split_points[i+1] * sampling_rate_target)
        chunk = speech_array[start:end]
        
        # Handle empty chunks (if any)
        if len(chunk) == 0:
            continue
        
        # Extract features and transcribe
        input_features = feature_extractor(
            chunk, 
            sampling_rate=sampling_rate_target, 
            return_tensors="pt"
        ).input_features.to(device)
        
        predicted_ids = model.generate(input_features)[0]
        transcription = processor.decode(predicted_ids, skip_special_tokens=True)
        transcriptions.append(transcription)
    
    full_transcription = " ".join(transcriptions)
    
    if verbose:
        print("[ytdebunk-transcriber] Transcription complete!")
    
    return full_transcription