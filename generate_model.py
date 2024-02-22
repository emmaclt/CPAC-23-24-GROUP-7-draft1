from pathlib import Path
from typing import List
import markovify
import mido
from markovify import Chain
from mido import MidiFile, MidiTrack
from mido import Message, MetaMessage

state_size=3
dataset_directory=Path("./maestro-v3.0.0/2014")
chain_output=Path("./model.json")
MIDI_output=Path("./song.mid")
fix_input=MIDI_output
fixMIDI_output=Path("./fix_song.mid")





#ENCODE METHOD

def encode(file: mido.MidiFile) -> List[str]:
    notes = []

    for message in mido.merge_tracks(file.tracks):
        if message.type != "note_on":
            continue

        notes.append(str(message))

    return notes







#DECODE METHOD

def decode_meta_message(line: str) -> MetaMessage:
    args = line[12:-1].split(", ")
    message_type = args.pop(0)[1:-1]

    
    kwargs = {}

    for argument in args:
        key, value = argument.split("=")
        
        if value.startswith("'") and value.endswith("'"): # string, we gotta remove the quotes
            value = value[1:-1]
        elif value.isnumeric():
            value = int(value)

        kwargs[key] = value
    
    
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







#GENERATE MODEL

dataset = []
for filename in dataset_directory.iterdir():
    with mido.MidiFile(filename) as file:
        messages = encode(file)

    dataset.append(messages)

    print(f"Processed {filename}")

chain = markovify.Chain(dataset, state_size=state_size)

'''with open(chain_output, "w") as file:
    file.write(chain.to_json())

print(f"Successfully generated model from {dataset_directory}! Saved to {chain_output}")
'''
#saving the chain is disabled because it exceeds the 100Mb github limit for 
#files dimention, not allowing to commit any change while updating the code





#GENERATE SONG
'''
with open(chain_output, "r") as file:
    chain = Chain.from_json(file.read())
'''
text = chain.walk()
midi = decode(text)
midi.save(MIDI_output)
print(f"Successfully generated song as {MIDI_output}")





#FIX MIDI FILE 
max_ticks=100

midi = mido.MidiFile(fix_input)
messages = mido.MidiTrack()

time = 0
pending = {}

for message in mido.merge_tracks(midi.tracks):
    time += message.time

    messages.append(message)

    if message.type not in ("note_on", "note_off"):
        continue
    
    if message.velocity >= 1: # note turned on
        pending[message.note] = time
    elif message.type == "note_off" or message.velocity == 0: # note turned off
        pending.pop(message.note, None)
    
    for note, timestamp in pending.copy().items():
        if time - timestamp < max_ticks:
            continue
        
        messages.append(mido.Message(
            "note_on", 
            note=note,
            velocity=0,
            time=time - timestamp
        ))
        pending.pop(note)
        
midi.tracks = [messages]
midi.save(fixMIDI_output)
print(f"Successfully fixed midi saved as {fixMIDI_output}")