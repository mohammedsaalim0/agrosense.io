import sys
import os
print(f"Python Executable: {sys.executable}")
print(f"Python Path: {sys.path}")
try:
    import google.generativeai as genai
    print("Google Generative AI is INSTALLED.")
except ImportError:
    print("Google Generative AI is MISSING.")
