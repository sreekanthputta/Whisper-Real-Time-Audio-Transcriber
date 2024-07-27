import numpy as np
import speech_recognition as sr
import whisper
from queue import Queue
from multiprocessing import Process
from Microphone import Microphone

class Transcriber:
    def __init__(self, model="small", energy_threshold=1000, record_timeout=10, microphone=Microphone.MICROPHONE, add_to_queue_callback=None):
        self.model = model + ".en" if model != "large" else model
        self.record_timeout = record_timeout
        self.microphone = microphone
        self.data_queue = Queue()
        self.add_to_queue_callback = add_to_queue_callback
        self.audio_model = whisper.load_model(self.model)

        # Initialize the recognizer and microphone
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = energy_threshold
        self.recorder.dynamic_energy_threshold = False
        self.recorder.non_speaking_duration = 0.5
        self.recorder.pause_threshold = 0.5 # Set 0.1 for faster response
        self.recorder.phrase_threshold = 0.5

        device_index = sr.Microphone.list_microphone_names().index(self.microphone.value)
        self.source = sr.Microphone(sample_rate=16000, device_index=device_index)

    def record_callback(self, r, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        self.data_queue.put(data)

    def transcribe(self):
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        self.recorder.listen_in_background(self.source, self.record_callback, phrase_time_limit=self.record_timeout)

        print(f"Transcriber ready for {self.microphone}...")

        while True:
            try:
                if len(self.data_queue.queue)>1:
                    print("transcribing")
                    queue = list(self.data_queue.queue)
                    self.data_queue.queue.clear()
                    self.data_queue.put(queue[-1][-1024*16:])
                    audio_data = b''.join(queue)

                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                    text = self.audio_model.transcribe(audio=audio_np, fp16=False)['text'].strip()

                    if self.add_to_queue_callback:
                        self.add_to_queue_callback(text)
                    else:
                        print(f"{self.microphone}: {text}")
            except KeyboardInterrupt:
                break


def start_transcriber(microphone, add_to_queue_callback):
    transcriber = Transcriber(microphone=microphone, add_to_queue_callback=add_to_queue_callback)
    transcriber.transcribe()

def start_transcriber_in_background(microphone, add_to_queue_callback):    
    transcriber_process = Process(target=start_transcriber, args=(microphone, add_to_queue_callback))
    transcriber_process.start()
    transcriber_process.join()