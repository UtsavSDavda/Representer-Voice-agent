import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi.responses import StreamingResponse
import requests
from deepgram import Deepgram,Transcription
import openai
import io
from prompts import FILE_SELECTION_PROMPT,ANSWER_PROMPT
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
if not DEEPGRAM_API_KEY:
    raise ValueError("DeepGram API KEY is NOT PROVIDED!")

openai.api_key = os.getenv('OPENAI_API_KEY')

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str):
    user = get_login_data().get(username)
    print(password)
    print(user["hashed_password"])
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def get_login_data():
    """Gets the login data from the database."""
    user_data =  {
    "user@example.com": {
        "username": "user@example.com",
        "full_name": "John Doe",
        "hashed_password": str(pwd_context.hash("password")), 
    }
}
    return user_data

def select_document(query: str) -> str:
        response = openai.chat.completions.create(model="gpt-4o-mini",  
    messages=[{"role": "system", "content": "You are a helpful assistant."},
              {"role": "user", "content": FILE_SELECTION_PROMPT.format(query=query)}],
    temperature=0.7)
        print(response)
        answer = response.choices[0].message.content
        return answer
    
def generate_response(query: str, document: str = None) -> str:
    response = openai.chat.completions.create(model="gpt-4o-mini",
messages=[{"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": ANSWER_PROMPT.format(query=query,document=document)}],
temperature=0.7)
    print(response)
    answer = response.choices[0].message.content 
    return answer

def process_text(query:str) -> str:
    """"""
    try:
        docname = select_document(query)
        print("Document selected for answering:",docname)
        try:
            with open(docname,'r') as f:
                doc_content = f.read()
        except:
            with open("experience.txt","r") as f:
                doc_content = f.read()
        response = generate_response(query,document=doc_content)
        return response
    except Exception as e:
        return str(e)
    
app = FastAPI()

@app.post("/process-audio/")
async def process_audio(file: UploadFile = File(...)):
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
    }
    
    audio_data = await file.read()
    
    stt_response = requests.post(
        "https://api.deepgram.com/v1/listen?model=nova-2",
        headers=headers,
        data=audio_data
    )

    if stt_response.status_code != 200:
        return {"error": f"STT Error: {stt_response.text}"}
    
    transcription = stt_response.json()
    text_question = transcription["results"]["channels"][0]["alternatives"][0]["transcript"]
    
    text_answer = process_text(text_question)
    print(text_answer)
    
    tts_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    tts_headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    tts_payload = {
        "text": text_answer
    }
    
    tts_response = requests.post(tts_url, headers=tts_headers, json=tts_payload)
    
    if tts_response.status_code != 200:
        return {"error": f"TTS Error: {tts_response.text}"}
    
    return StreamingResponse(
        io.BytesIO(tts_response.content),
        media_type="audio/mp3"
    )

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_token({"sub": user["username"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_token({"sub": user["username"]}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        new_access_token = create_token({"sub": username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return {"access_token": new_access_token, "token_type": "bearer"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
