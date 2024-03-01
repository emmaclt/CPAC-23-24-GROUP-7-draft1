from pathlib import Path
from typing import List
import mido
from chain import Chain
from mido import MidiFile, MidiTrack
from mido import Message, MetaMessage
import pyOSC3
import time
from my_chain import VariableLengthMarkovChain


max_order=8
set_order=6
dataset_directory=Path("./maestro-v3.0.0/test")






#ENCODE METHOD

def encode(file: mido.MidiFile) -> List[str]:
    notes = []

    for message in mido.merge_tracks(file.tracks):
        if message.type != "note_on":
            continue

        notes.append(str(message))

    return notes









#GENERATE MODEL

dataset = []
for filename in dataset_directory.iterdir():
    with mido.MidiFile(filename) as file:
        messages = encode(file)

    dataset.extend(messages)

    print(f"Processed {filename}")


dataset_notes=[int(s.split('note=')[1].split(' ')[0]) for s in dataset]
dataset_velocity=[int(s.split('velocity=')[1].split(' ')[0]) for s in dataset]
dataset_time=[int(s.split('time=')[1].split(' ')[0]) for s in dataset]


markov_chain_notes = VariableLengthMarkovChain(max_order, dataset_notes)
markov_chain_velocity = VariableLengthMarkovChain(max_order, dataset_velocity)
markov_chain_time = VariableLengthMarkovChain(max_order, dataset_time)









#GENERATE NOTES

client = pyOSC3.OSCClient()
client.connect( ( '127.0.0.1', 7001 ) )
state_notes = tuple(dataset_notes[0:set_order])
state_velocity = tuple(dataset_velocity[0:set_order])
state_time = tuple(dataset_time[0:set_order])


while True:
    next_state_notes = markov_chain_notes.generate(state_notes, set_order)
    next_state_velocity = markov_chain_velocity.generate(state_velocity, set_order)
    next_state_time = markov_chain_time.generate(state_time, set_order)
    #update current state with next state requires the tuple to be converted to list,
    #manipulated and converted back to tuple
    update_state_notes=list(state_notes)
    update_state_notes.pop(0)
    update_state_notes.append(next_state_notes)
    state_notes=tuple(update_state_notes)

    update_state_velocity=list(state_velocity)
    update_state_velocity.pop(0)
    update_state_velocity.append(next_state_velocity)
    state_velocity=tuple(update_state_velocity)

    update_state_time=list(state_time)
    update_state_time.pop(0)
    update_state_time.append(next_state_time)
    state_time=tuple(update_state_time)
    #control generation/printing flow (currentlty every 1 second)
    print("Note: "+str(next_state_notes)+" velocity: "+str(next_state_velocity)+" time: "+str(next_state_time))

    msg = pyOSC3.OSCMessage()
    msg.setAddress("/0")
    out=[next_state_notes, next_state_velocity, next_state_time]
    msg.append(out)
    client.send(msg)

    time.sleep(1)

