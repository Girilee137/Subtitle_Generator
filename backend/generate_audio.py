import pyttsx3
engine = pyttsx3.init()
engine.save_to_file('Hello world, this is a test of the GPU transcription system. It should be very fast.', 'sample_speech.wav')
engine.runAndWait()
print('Generated sample_speech.wav')
