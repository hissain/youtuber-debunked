# ytdebunk  

## Overview  
`ytdebunk` is a command-line tool designed to:  
- Download audio from YouTube videos.  
- Transcribe the audio content.  
- Optionally enhance the transcription using the **Gemini API**.  

This tool is particularly useful for analyzing transcriptions to identify **logical fallacies** and **incorrect claims** made by YouTubers.  

## Installation  

To install the required dependencies, run:  

```sh
pip install -r requirements.txt
```

## Usage  

The `ytdebunk.py` script provides a **command-line interface (CLI)** with several options.  

### **Arguments**  
- `video_url` (**str**) – URL of the YouTube video to download audio from.  

### **Options**  
| Option                  | Description |
|-------------------------|-------------|
| `-e, --enhance` (bool) | Enhance the transcription using the **Gemini API**. *(Default: False)* |
| `-o, --output_file` (str) | Path to save the final transcription. *(Default: `downloads/transcription.txt`)* |
| `-v, --verbose` (bool) | Increase output verbosity. |
| `-t, --token` (str) | API token for the **Gemini API** *(Required if `--enhance` is enabled)*. |

### **Example Usage**  

```sh
python ytdebunk.py "https://www.youtube.com/watch?v=example" -e -o output.txt -v -t YOUR_GEMINI_API_TOKEN
```

## **Environment Variables**  
If preferred, you can set the **Gemini API token** as an environment variable instead of passing it as a CLI argument:

```sh
export GEMINI_API_TOKEN="your_api_key"
```

## **Detailed Process**  

1. **Download Audio**  
   - Uses the `download_audio` function from `ytdebunk.downloader` to download audio from the given YouTube URL.  

2. **Transcribe Audio**  
   - Uses the `transcribe_audio` function from `ytdebunk.transcriber` to generate a text transcription.  

3. **Enhance Transcription** *(Optional)*  
   - If `--enhance` is enabled, the script uses `enhance_transcription` from `ytdebunk.refiner` to refine the transcription using the **Gemini API**.  
   - The API token must be provided via `--token` or as an **environment variable**.  

4. **Save Transcription**  
   - The final transcription (raw or enhanced) is saved to the specified output file.  

## **Error Handling**  
- If `--enhance` is enabled but no **Gemini API token** is provided, the script prints an **error message** and exits.  

## **License**  
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.  

