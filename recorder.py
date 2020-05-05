import sys
import os
import time
import math
import audioop
from datetime import datetime
from collections import deque

import pyaudio
import wave

CHUNK = 2000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 300
SILENCE_LIMIT = 2
PREV_AUDIO = 2


def listen_command(stream, threshold=THRESHOLD):
    print("* Listening mic. ")
    cur_data = ''
    rel = RATE / CHUNK
    slid_win = deque(maxlen=int(SILENCE_LIMIT * rel))
    prev_audio = deque(maxlen=int(PREV_AUDIO * rel))
    started = False
    result = []

    while True:
        cur_data = stream.read(CHUNK)
        slid_win.append(math.sqrt(abs(audioop.avg(cur_data, 4))))
        if(sum([x > THRESHOLD for x in slid_win]) > 0):
            if(not started):
                print("Starting record of phrase")
                started = True
                result = list(prev_audio)
            result.append(cur_data)
        elif (started is True):
            print("Finished")
            break
        else:
            prev_audio.append(cur_data)

    print("* Done recording")
    return result


if len(sys.argv) == 2:
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    try:
        while True:
            data = listen_command(stream)
            name = str(int(datetime.now().timestamp() * 100000)) + '.wav'
            wf = wave.open(os.path.join(sys.argv[1], name), 'wb')
            print(f'{name} opened')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            for chunk in data:
                wf.writeframesraw(chunk)
            wf.close()
            print(f'{name} closed')
    except KeyboardInterrupt:
        stream.close()
        p.terminate()
        print('Завершение работы!\n\n')
