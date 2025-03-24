# Representer-Voice-agent

A voice agent that represents me (or you, depending on its data) in conversations. Like an interactive audio based resume.

# What this project means?
This project is a sort of an audio-resume. It is a voice based bot that answers your questions about a candidate including his/her technical/leadership/general attitude aspects.

It contains 3 files as Source data, using which the LLM can answer any question regarding the user.

The bot will convert your questions from audio to text (using Speech-to-text/STT services), then answering your question by passing it to 2 LLM calls: one LLM call to decide which aspect of the candidate (me) you want to search about, and the 2nd LLM call that shall read the particular file about the chosen aspect and answering your query using it's data.

Finally, the bot answers back in a voice using Text-to-speech (TTS) services to convert the textual answer to an audio file.

This bot shall be interactive and I will try my level best to improve it's time complexity.
