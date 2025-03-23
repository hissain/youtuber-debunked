from setuptools import setup, find_packages

setup(
    name="ytdebunk",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv",
        "google-generativeai",
        "yt-dlp",
        "torch",
        "torchaudio",
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
        "geminai"
        ],
)