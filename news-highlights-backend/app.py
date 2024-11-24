from flask import Flask, request, jsonify
from flask_cors import CORS
import assemblyai as aai
import requests
import os
import yt_dlp


app = Flask(__name__)
CORS(app)

# Set your AssemblyAI API key
aai.settings.api_key = "ae21c450a8354e588dc1c1a5362aba34"
transcriber = aai.Transcriber()

@app.route('/api/highlights', methods=['POST'])
def get_highlights():
    youtube_url = request.form.get('youtubeUrl')
    audio_file = request.files.get('audioFile')

    try:
        if youtube_url:
            # Handle YouTube URL 
            ydl_opts = {
                'format': 'm4a/bestaudio/best',  # The best audio version in m4a format
                'outtmpl': '%(id)s.%(ext)s',  # The output name should be the id followed by the extension
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
                info_dict = ydl.extract_info(youtube_url, download=False)
                audio_file_path = f"{info_dict['id']}.m4a"
                print(f"Downloaded audio file to {audio_file_path}")

            # Transcribe the audio file using AssemblyAI
            transcript = transcriber.transcribe(audio_file_path)
            print(f"Transcript: {transcript}")

            # Generate highlights using the transcript
            prompt = "Can you give a brief highlights of the given news article in bullet points."
            result = transcript.lemur.task(prompt, final_model=aai.LemurModel.claude3_5_sonnet)
            print(f"Highlights: {result}")

            # Clean up the downloaded file
            os.remove(audio_file_path)
            print(f"Removed audio file {audio_file_path}")

            return jsonify({'highlights': result.response}), 200


        if audio_file:
            # Save the uploaded audio file
            audio_path = os.path.join('uploads', audio_file.filename)
            audio_file.save(audio_path)

            # Transcribe the audio file using AssemblyAI
        transcript = transcriber.transcribe(audio_path)

        # Generate highlights using the transcript
        prompt = "Can you give a brief highlights of the given news article in bullet points."
        result = transcript.lemur.task(prompt, final_model=aai.LemurModel.claude3_5_sonnet)

        # Clean up the uploaded file
        os.remove(audio_path)

        return jsonify({'highlights': result.response})

        # return jsonify({'error': 'No input provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(port=5000)