import os 
from dotenv import load_dotenv

load_dotenv(override=True)
key = os.getenv("GROQ_API_KEY")
print(repr(key))
print("Length:", len(key))