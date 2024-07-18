import streamlit as st
from groq import Groq
import tempfile
import os
from moviepy.editor import VideoFileClip

st.set_page_config(
    page_title="MoM Generator",
    page_icon="🤖",
)

# Initialize Groq client
client = Groq(api_key=st.secrets["token"])

def video_to_audio(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video_file:
        tmp_video_file.write(video_file.getvalue())
        video_path = tmp_video_file.name

    audio_path = video_path.rsplit('.', 1)[0] + ".mp3"
    
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
    except Exception as e:
        st.error(f"An error occurred during video-to-audio conversion: {str(e)}")
        return None
    finally:
        os.unlink(video_path)

    return audio_path

def speech_to_text(file_path):
    try:
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
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
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)

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
st.write("Upload your audio or video file (Hindi, English), Get the MoM from this tool in seconds! Max Size for file is 25Mb! Still in Beta...")

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
uploaded_file = st.file_uploader("Upload an audio or video file", type=["mp3", "wav", "m4a", "mp4", "avi", "mov"])

if uploaded_file is not None:
    file_type = uploaded_file.type.split('/')[0]
    
    if file_type == 'video':
        st.video(uploaded_file)
    elif file_type == 'audio':
        st.audio(uploaded_file)

    if st.button("Generate MoM"):
        with st.spinner("Processing file..."):
            if file_type == 'video':
                audio_file_path = video_to_audio(uploaded_file)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split('.')[-1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    audio_file_path = tmp_file.name

            if audio_file_path:
                transcription = speech_to_text(audio_file_path)

                if transcription:
                    with st.spinner("Generating MoM..."):
                        mom = generate_mom(system_prompt, transcription)
                    if mom:
                        st.subheader("Result of MoM:")
                        st.markdown(mom)
                else:
                    st.error("Transcription failed. Please try again with a different file.")
            else:
                st.error("File processing failed. Please try again with a different file.")

st.sidebar.header("About")
st.sidebar.info("This app generates Minutes of Meeting (MoM) from uploaded audio or video files using AI powered technology. Currently it is working for Hindi and English Audio Files!")
