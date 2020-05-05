import sys
import os
import time

import pyaudio
import wave

from vosk import Model, KaldiRecognizer
from text_analyser import TextAnalyser

model = Model(os.path.join('..', 'model'))
analyzer = TextAnalyser(os.path.join('demo', 'goods_list.csv'), bag_code='11111111111')


def create_log_message(processed, counter):
    log_message = f'\nDEBUG: {counter}: '
    shift = len(log_message)
    is_first = True
    for k, v in processed.items():
        if is_first:
            log_message += f'{k}: {v}\n'
            is_first = False
        else:
            log_message += f'{" " * (shift - 1)}{k}: {v}\n'
    log_message += '===========\n'

    return log_message


if len(sys.argv) > 2:
    print('Invalid number of arguments, pas either no arguments (for microphone usage) or records directory path')
    sys.exit(1)

if len(sys.argv) == 2:
    dir_path = sys.argv[1]
    try:
        counter = 0
        while True:
            file_paths = [p for p in os.listdir(dir_path) if p.endswith('.wav')]

            if len(file_paths) > 0:
                file_path_to_process = os.path.join(dir_path, file_paths[0])
                wf = wave.open(file_path_to_process, 'rb')
                rec = KaldiRecognizer(model, wf.getframerate())

                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break

                    if rec.AcceptWaveform(data):
                        continue

                text = eval(rec.FinalResult())['text']

                if len(text) > 0:
                    print()
                    counter += 1

                    processed = analyzer.parse(text)
                    log_message = create_log_message(processed, counter)

                    if text.startswith('заверш'):
                        splitted = text.split(' ')
                        if len(splitted) == 2 and splitted[1].startswith('работ'):
                            print('Завершение работы!\n\n')
                            break
                        print(log_message)
                        continue

                    print(log_message)

                os.remove(file_path_to_process)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print('Завершение работы!\n\n')
else:
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    rec = KaldiRecognizer(model, 16000)

    counter = 0
    while True:
        data = stream.read(4000)
        if len(data) == 0:
            break

        elif rec.AcceptWaveform(data):
            text = eval(rec.Result())['text']

            if len(text) > 0:
                print()
                counter += 1

                processed = analyzer.parse(text)
                log_message = create_log_message(processed, counter)

                if text.startswith('заверш'):
                    splitted = text.split(' ')
                    if len(splitted) == 2 and splitted[1].startswith('работ'):
                        print('Завершение работы!\n\n')
                        break
                    print(log_message)
                    continue

                print(log_message)
        else:
            pass
