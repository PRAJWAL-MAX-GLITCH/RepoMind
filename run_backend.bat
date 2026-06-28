@echo off
set PATH=%PATH%;C:\Users\prajw\.local\bin
cd /d "d:\Project Aiml\RepoMind\private-gpt-main\private-gpt-main"
uv sync --extra core
set OPENAI_API_BASE=http://localhost:11434/v1
set OPENAI_EMBEDDING_API_BASE=http://localhost:11434/v1
uv run repomind serve
