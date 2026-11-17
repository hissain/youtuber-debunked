from setuptools import setup, find_packages

setup(
    name="ytdebunk",
    version="1.5.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={"ytdebunk": ["static/*"]},
    install_requires=[
        "numpy",
        "python-dotenv==1.0.1",
        "pydantic>=2.10.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "google-genai>=3.0.0",
        "google-generativeai==0.8.4",
        "ddgs>=9.0.0",
        "duckduckgo-search>=8.0.0",
        "edge-tts>=7.0.0",
        "mutagen>=1.47.0",
        "pillow>=10.0.0",
        "moviepy>=2.1.0",
        "yt-dlp==2025.3.21",
        "torch==2.1.0",
        "torchaudio==2.1.0",
        "librosa==0.11.0",
        "transformers==4.36.2",
    ],
    entry_points={
        "console_scripts": [
            "ytdebunk=ytdebunk.ytdebunk:main",
            "ytdebunk-studio=ytdebunk.server:run"
        ]
    },
    author="Md. Sazzad Hissain Khan",
    author_email='hissain.khan@gmail.com',
    description="A CLI tool to automatically download audio .mp3 from a YouTube video link, transcribe it, refine and find logical errors in the transcription using AI.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/hissain/youtuber-debunked',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=[
        "youtube", 
        "transcription", 
        "audio", 
        "refinement", 
        "ai",
        "bengali", 
        "geminai",
        "librosa",
        "streamlit",
        ],
)