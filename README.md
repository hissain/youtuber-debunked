# ytdebunk

## Overview

`ytdebunk` is a command-line tool that can be installed via `pip`. This repository contains the source code and a demonstration of its features.

### Current Features:
- Download audio from YouTube videos.
- Transcribe the audio content.
- Optionally enhance the transcription using the **Gemini API**.
- Optionally detect logical faults in the transcription using the **Gemini API**.
- A Streamlit-based demo application.

### Upcoming Features:
- Classifying assertive claims within the transcription.
- Fact-checking and validating claims using online searches and agentic AI.
- Categorizing factual and logical faults.
- Generating a script for a hypothetical debunker character using generative AI (or AI Agents).
- Synthesizing the script into audio and video using generative AI (or AI Agents).

This tool is particularly useful for analyzing transcriptions to identify **logical fallacies** and **incorrect claims** made by YouTubers, helping to prepare debunk videos.

## Installation

To avoid conflicts, it is recommended to create a virtual environment:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
```

Now, install `ytdebunk` from PyPI:

```sh
pip install ytdebunk
```

Alternatively, install the latest version directly from GitHub:

```sh
pip install git+https://github.com/hissain/youtuber-debunked.git
```

## Usage (CLI Tool)

`ytdebunk` is a **command-line interface (CLI)** with multiple options.

### **Arguments**
- `video_url` (**str**) – URL of the YouTube video to extract audio from.

### **Options**
| Option                  | Description |
|-------------------------|-------------|
| `-l, --language` (str) | Language code for transcription. Supported: [bn, en] (default: en) |
| `-e, --enhance` (bool) | Enhance the transcription using the **Gemini API** (default: False) |
| `-d, --detect` (bool) | Detect logical faults using the **Gemini API** (default: False) |
| `-v, --verbose` (bool) | Enable verbose logging. |
| `-t, --token` (str) | API token for **Gemini API** *(Required if `--enhance` or `--detect` is enabled)* |
| `-st, --start_time` (float) | Start time of the audio clip (seconds) |
| `-et, --end_time` (float) | End time of the audio clip (seconds) |
| `-m, --model` (str) | Transcription model from Hugging Face (WhisperFeatureExtractor) |

#### **Example Usage**

```bash
ytdebunk "https://www.youtube.com/watch?v=example" -e -d -v -t YOUR_GEMINI_API_TOKEN
```

Alternatively, using an environment variable:

```bash
export GEMINI_API_TOKEN="your_api_key"
ytdebunk "https://www.youtube.com/watch?v=example" -e -d -v
```

For more examples, check the [Example Notebook](experiment/exp.ipynb).

## Usage (Streamlit App)

To run the demo using Streamlit:

1. Install Streamlit:

```bash
pip install streamlit
```

2. Run the application:

```bash
streamlit run app.py
```

### Screenshots of the Streamlit App

![Query Fields English](assets/Screenshot_Q_e.png)
![Transcription Result English](assets/Screenshot_R_e.png)
![Query Fields Bangla](assets/Screenshot_Q.png)
![Transcription Result Bangla](assets/Screenshot_R.png)
![Logical Faults Detected Bangla](assets/Screenshot_F.png)

## **Environment Variables**

Set the **Gemini API token** as an environment variable:

```sh
export GEMINI_API_TOKEN="your_api_key"
```

## **Detailed Process**

1. **Download Audio**
   - Uses `ytdebunk.downloader.download_audio` to download audio from the given YouTube URL.

2. **Transcribe Audio**
   - Uses `ytdebunk.transcriber.transcribe_audio` to generate a text transcription.

3. **Enhance Transcription** *(Optional)*
   - If `--enhance` is enabled, `ytdebunk.refiner.enhance_transcription` refines the transcription using the **Gemini API**.
   - The API token must be provided via `--token` or as an **environment variable**.

4. **Detect Logical Faults** *(Optional)*
   - If `--detect` is enabled, `ytdebunk.philosopher.detect_logical_faults` identifies logical faults, fallacies, biases, irony, etc., using the **Gemini API**.
   - The API token must be provided via `--token` or as an **environment variable**.

5. **Save Transcription**
   - The final audio, transcription, and detected logical faults (raw or enhanced) are saved to the `./output` folder.

## **Error Handling**
- If `--enhance` or `--detect` are enabled but no **Gemini API token** is provided, the script exits with an error message.

## **License**
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## **Contribution & Contact**

Contributions are welcome! Fork the project and submit a pull request to add new features or improve existing ones.

For inquiries, contact the project author at **hissain.khan@gmail.com**.
