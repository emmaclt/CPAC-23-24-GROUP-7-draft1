from pathlib import Path
from typing import List
import mido
import pyOSC3
import time
from my_chain import VariableLengthMarkovChain
from threading import Thread
import re
from mido import MidiFile, MidiTrack
from mido import Message, MetaMessage

max_order=5
set_order=5
dataset_directory=Path("./maestro-v3.0.0/test")



#ENCODE METHOD

def encode(file: mido.MidiFile) -> List[str]:
    notes = []

    for message in mido.merge_tracks(file.tracks):
        if message.type != "note_on":
            continue

        notes.append(str(message))

    return notes



# Function to set the tempo and the bpm of the dataset midi files 

def setup_time(file: mido.MidiFile):
    for message in file:
        if message.type == 'set_tempo':
            tempo = message.tempo
            bpm = mido.tempo2bpm(tempo)
            break

    return tempo, bpm



#GENERATE MODEL

dataset_notes = []

for filename in dataset_directory.iterdir():
    with mido.MidiFile(filename) as file:
        notes = encode(file)

    dataset_notes.extend(notes)
    print(f"Processed {filename}")    


with open("Input.txt", "w") as text_file:
    print(f"Note: "+str(dataset_notes), file=text_file)

print(len(dataset_notes))


#set tempo, bpm and ticks per beat
first_file_midi = next(dataset_directory.iterdir())
with mido.MidiFile(first_file_midi) as file:
    tempo, bpm = setup_time(file)
    ticks_per_beat = file.ticks_per_beat

print(tempo, bpm, ticks_per_beat)



# Function to menage the received OSC messages
def handle_message(address, tags, data, client_address):
    global set_order
    set_order = data[0]
    print(f"Ricevuto messaggio da {address}: {set_order}")


# Function to run the server in a separated thread
def run_server():
    
    server = pyOSC3.OSCServer(("127.0.0.1", 57000))
    server.addMsgHandler("/closeness", handle_message)

    print(f"In ascolto")
    
    # Run the server
    server.serve_forever()

server_thread = Thread(target=run_server)
server_thread.start()


markov_chain_notes = VariableLengthMarkovChain(max_order, dataset_notes)





#GENERATE NOTES

client = pyOSC3.OSCClient()
client.connect( ( '127.0.0.1', 57120 ) )
state_notes = tuple(dataset_notes[0:set_order])
all_states=[]
all_states.extend(list(state_notes))
text=[]

#initialize output file to blank (file per controllare se le stringhe generate hanno senso)
with open("Output.txt", "w") as text_file:
        print(f"", file=text_file)

i=0

while i<1000:
    print(set_order)
    state_notes=tuple(all_states[(len(all_states)-set_order):len(all_states)])
    next_state_notes = markov_chain_notes.generate(state_notes, set_order)
    all_states.append(next_state_notes)

    #effettiva scrittura del file di controllo 
    with open("Output.txt", "a") as text_file:
        print(f"Note: "+str(next_state_notes), file=text_file)

    text.append(str(next_state_notes))
    #print("Note: "+str(next_state_notes))
    
    with open("state_notes.txt", "a") as text_file:
        print(f"Note: "+str(state_notes), file=text_file)

    #divide string and extract numbers to be sent via OSC
    temp = re.findall(r'\d+', next_state_notes)
    res = list(map(int, temp))
    next_state_notes=res[1]
    next_state_velocity=res[2]
    next_state_time=res[3]

    #prepare the message
    msg = pyOSC3.OSCMessage()
    msg.setAddress("/numbers")
    out=[next_state_notes, next_state_velocity, next_state_time]
    msg.append(out)
    
    #compute the delta time, it's the time that should pass between the last note played and the current note
    delta_time = mido.tick2second(next_state_time, ticks_per_beat, tempo*2)
    print(delta_time)
    time.sleep(delta_time)

    #print and send
    print(res)
    client.send(msg)


    i=i+1
    
    









def decode_meta_message(line: str) -> MetaMessage:
    args = line[12:-1].split(", ")
    message_type = args.pop(0)[1:-1]

    #args = [argument.split("=") for argument in args]
    kwargs = {}

    for argument in args:
        key, value = argument.split("=")
        
        if value.startswith("'") and value.endswith("'"): # string, we gotta remove the quotes
            value = value[1:-1]
        elif value.isnumeric():
            value = int(value)

        kwargs[key] = value
    
    #print(f"Decoded meta message: {message_type} {kwargs}")
    return MetaMessage(message_type, **kwargs)

def decode(text: List[str]) -> MidiFile:
    track = MidiTrack()

    for line in text:
        if line.startswith("MetaMessage"):
            track.append(decode_meta_message(line))
            continue

        try:
            track.append(Message.from_str(line))
        except:
            print(f"Failed to decode message: {line}")
    
    return MidiFile(tracks=[track])


MIDI_output=Path("./song.mid")
midi = decode(text)
midi.save(MIDI_output)

