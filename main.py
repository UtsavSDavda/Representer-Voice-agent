import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import requests
from deepgram import Deepgram,Transcription
import openai
import io
import streamlit as st
from prompts import FILE_SELECTION_PROMPT,ANSWER_PROMPT

DEEPGRAM_API_KEY = st.secrets['DEEPGRAM_API_KEY']
if not DEEPGRAM_API_KEY:
    raise ValueError("DeepGram API KEY is NOT PROVIDED!")

openai.api_key = st.secrets['OPENAI_API_KEY']

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
