from multiprocessing import Process, Queue

from Microphone import Microphone
from transcriber import Transcriber

transcription_queue = Queue()

def run_transcriber(microphone, queue):
    transcriber = Transcriber(model="small", microphone=microphone, add_to_queue_callback=lambda text: queue.put({"from": microphone.name, "message": text}))
    transcriber.transcribe()

def start_transcribers(queue):
    """Start the transcribers in background processes."""
    for microphone in [Microphone.MICROPHONE, Microphone.SPEAKER]:
        thread = Process(target=run_transcriber, args=(microphone, queue,))
        thread.start()
        # thread.join()

# def send_realtime_transcription_via_socket():
#     while True:
#         if not transcription_queue.empty():
#             transcript = transcription_queue.get()
#             socketio.emit('transcription', transcript)
#         socketio.sleep(1)

def send_realtime_transcription_via_terminal(queue):
    while True:
        if not queue.empty():
            transcript = queue.get()
            print(f"Transcription from {transcript['from']}: {transcript['message']}")

if __name__ == '__main__':
    # Printing using queues from Multiprocessing
    start_transcribers(transcription_queue)
    thread = Process(target=send_realtime_transcription_via_terminal, args=(transcription_queue,))
    thread.start()
    thread.join()

    # Sending transcript to frontend using Flask-SocketIO
    # socketio.start_background_task(send_realtime_transcription_via_socket)
    