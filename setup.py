from setuptools import setup, find_packages

setup(
    name="ytdebunk",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "numpy<2",
        "python-dotenv==1.0.1",
        "google-generativeai==0.8.4",
        "yt-dlp==2025.3.21",
        "torch==2.1.0",
        "torchaudio==2.1.0",
        "librosa==0.11.0",
        "transformers==4.36.2",
    ],
    entry_points={"console_scripts": ["ytdebunk=ytdebunk.ytdebunk:main"]},
    author="Md. Sazzad Hissain Khan",
    author_email='hissain.khan@gmail.com',
    description="A CLI tool to download audio from a YouTube video, transcribe it, and refine the transcription using AI.",
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
        "bangla", 
        "bengali", 
        "geminai",
        "librosa",
        ],
)