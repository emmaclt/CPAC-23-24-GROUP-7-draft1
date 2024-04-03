from pathlib import Path
from typing import List
import mido
import pyOSC3
import time
from my_chain_fe import VariableLengthMarkovChain
from threading import Thread
import re

max_order=3
set_order=3
dataset_directory=Path("./maestro-v3.0.0/2018")



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

    dataset_notes.append(notes)

    print(f"Processed {filename}")


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
state_notes = tuple(dataset_notes[0][0:set_order])


#initialize output file to blank (file per controllare se le stringhe generate hanno senso)
with open("Output.txt", "w") as text_file:
        print(f"", file=text_file)


while True:
    print(set_order)
    next_state_notes = markov_chain_notes.generate(state_notes, set_order)

    #update current state with next state requires the tuple to be converted to list,
    #manipulated and converted back to tuple
    update_state_notes=list(state_notes)
    update_state_notes.pop(0)
    update_state_notes.append(next_state_notes)
    state_notes=tuple(update_state_notes)

   #effettiva scrittura del file di controllo 
    with open("Output.txt", "a") as text_file:
        print(f"Note: "+str(next_state_notes), file=text_file)

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
    delta_time = mido.tick2second(next_state_time, ticks_per_beat, tempo*4)
    print(delta_time)
    time.sleep(delta_time)

    #print and send
    print("Note: "+str(next_state_notes))
    print(res)
    client.send(msg)

    
    
    

