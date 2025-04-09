# Representer-Voice-agent

A voice agent that represents me (or you, depending on its data) in conversations. Like an interactive audio based resume.

# What this project means?
This project is a sort of an audio-resume. It is a voice based bot that answers your questions about a candidate including his/her technical/leadership/general attitude aspects.

It contains 3 files as Source data, using which the LLM can answer any question regarding the user.

The bot will convert your questions from audio to text (using Speech-to-text/STT services), then answering your question by passing it to 2 LLM calls: one LLM call to decide which aspect of the candidate (me) you want to search about, and the 2nd LLM call that shall read the particular file about the chosen aspect and answering your query using it's data.

Finally, the bot answers back in a voice using Text-to-speech (TTS) services to convert the textual answer to an audio file.

This bot shall be interactive and I will try my level best to improve it's time complexity.

# How to use this app?

Step 1: Clone this repository, or download it and place it inside a folder in your PC.

Step 2: Enter your API keys. Create a .env file in your directory where you have placed these files. Enter OPENAI_API_KEY and DEEPGRAM_API_KEY inside it. This project requires these 2 API keys to run.

Step 3: You will have 3 files: experience.txt, personality.txt and skills.txt. Please enter your details about your experience, personality and skills in these files as the chatbot will be answering user questions using data from these files.

Step 4: Run the app. Open 2 terminals. Enter the following command in the first terminal:

uvicorn localmain:app --reload

Enter the following command in the 2nd terminal: 

streamlit run app.py

Step 5: Use your app! Open any browser. Enter the following URL:  localhost:8501.

NOTE: Use the following username and password:

Username: user@example.com
Password: password

You will see a screen of streamlit UI. Press start recording to ask your question. Press stop recording once you are done. You will recieve an audio response. Play it to hear the response.

![image](https://github.com/user-attachments/assets/438ddcba-4c92-4bb8-a07d-06c72e9a17ab)

Thanks for using this app. Please help me improve it with your feedback!
