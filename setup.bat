@echo off
echo === Installing Eli-Lain-Ai-Tracker ===
python -m venv .venv
.venv\Scripts\activate
pip install -e .
echo Done. Run: python main.py
