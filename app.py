import streamlit as st
from groq import Groq
import tempfile
import os

st.set_page_config(
    page_title="MoM Generator",
    page_icon="🤖",
)

# Initialize Groq client
client = Groq(api_key=st.secrets["token"])

def speech_to_text(audio_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(audio_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        with open(tmp_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(tmp_file_path, file.read()),
                model="whisper-large-v3",
                prompt="Specify context or spelling",
                response_format="json",
                language="en",
                temperature=0.0
            )
        return transcription.text
    except Exception as e:
        st.error(f"An error occurred during transcription: {str(e)}")
        return None
    finally:
        os.unlink(tmp_file_path)

def generate_mom(system, prompt):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred during MoM generation: {str(e)}")
        return None

# Streamlit UI
st.title("AI-Powered MoM Generator")
st.write("Upload your audio file(Hindi, English), Get the MoM from this tool in seconds! Max Size for file is 25Mb! Still in Beta...")

# System prompt
system_prompt = """
You will receive the translation of a meeting audio and need to analyze that translation to create the Minutes of Meeting (MoM). 

Provide only the MoM in the following format:

### Minutes of Meeting (MoM):
(Leave this blank)

### Attendees:
(Leave this blank)

### Meeting Notes/Tasks:
- Analyze the translation and list down the notes and discussion points of the meeting.
- This section should be in bullet points only.

### Tasks:
- Analyze the translation and list down the tasks from the meeting.
- This section should be in bullet points only.
- Provide detailed descriptions of each task.

----------------------

Provide only the MoM in the specified format.

"""

# File uploader
uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/mp3")

    if st.button("Generate MoM"):
        with st.spinner("Transcribing audio..."):
            transcription = speech_to_text(uploaded_file)

        if transcription:
            # st.subheader("Transcription:")
            # st.write(transcription)

            with st.spinner("Generating MoM..."):
                mom = generate_mom(system_prompt, transcription)

            if mom:
                st.subheader("Result of MoM:")
                st.markdown(mom)

st.sidebar.header("About")
st.sidebar.info("This app generates Minutes of Meeting (MoM) from uploaded audio files using AI powered technology. Currently it is working for Hindi and English Audio Files!")
