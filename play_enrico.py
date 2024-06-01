from pathlib import Path    # to handle filesystem paths 
from typing import List
import mido                 # to work with MIDI messages and files
import pyOSC3               # !!! communication handled using pyOSC3 (Open Sound Control messages)
import time
from my_chain import VariableLengthMarkovChain      # imports the markov chain class to use it in music generation
from threading import Thread                        # to create a manage threads
import re                                   # provides regular expression matching operations


#PARAMETERS------------------------------------------------------------------------------

max_order=8             # markov chain maximum order
set_order=1             # initial order to be used to generate sequencies in the markov chain
velocity_quantization=16        # quantization level for MIDI 'velocity' (force with which a note is played)
time_quantization=64            # quantization level for timing of the notes
dur_quantization=64             # quantization level for duration of the notes
tempo_modifier=1                # modifier of the tempo of the generated music 

dataset_directory=Path("./maestro-v3.0.0/2017")         # path to the MIDI files dataset



#SETUP-----------------------------------------------------------------------------------

# section to setup functions used to handle MIDI files 

#Function to encode MIDI files into strings
def encode(file: mido.MidiFile) -> List[str]: # returns a list of strings representing 'note_on' messages
    notes = []      # list to store note messages

    for message in mido.merge_tracks(file.tracks):      # merges all tracks in the midi file into a single sequence of messages
        if message.type != "note_on":                   # filtering out messages that are not 'notes_on'
            continue

        notes.append(str(message))      # 'notes_on' message converted to a string and added to 'notes' list

    return notes            # list of encoded 'note_on' messages

#Function to set the tempo and the bpm of the dataset MIDI files 
def setup_time(file: mido.MidiFile):
    for message in file:        # iteration over all messages in the midi file
        if message.type == 'set_tempo':         # searches for 'set_tempo' messages in the MIDI file
            tempo = message.tempo
            bpm = mido.tempo2bpm(tempo)         # converts the tempo into bpm 
            break

    return tempo, bpm           # returns tempo and bpm of the MIDI file


#Function to map variables from one range to another -> returns the mapped value
def range_map(OldMax, OldMin, NewMax, NewMin, OldValue):
    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)  
    NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
    return NewValue

#Function to manage the received OSC message for closeness (which will set the order for the Variable Markov Chain)
def handle_message(address, tags, data, client_address):
    global set_order        # allows the function to modify the order of the markov chain
    set_order = data[0]     # i'm guessing the first element of the data array holds the 'closeness' parameter 
    
    print(f"Ricevuto messaggio da {address}: {set_order}")      # to debug, prints address and the order just set 

#Function to run the server in a separated thread
def run_server():
    server = pyOSC3.OSCServer(("127.0.0.1", 57000))     # sets up the OSC server  
    server.addMsgHandler("/closeness", handle_message)  # registers 'handle_message' as the handler for messages with the addres '/closeness'
    print(f"In ascolto")
    # Run the server
    server.serve_forever()      # starts the OSC server handling incoming messages (it will run indefinitely)



#MIDI PROCESSING-------------------------------------------------------------------------

dataset_notes = []      # to store encoded MIDI notes
notes_int=[]            # to store MIDI note information (converted to 'int' from 'string')
notes_int_dur=[]        # 

#Read midi files, encode and store data in dataset_notes
for filename in dataset_directory.iterdir():        # iterates over all files in the dataset
    with mido.MidiFile(filename) as file:           
        notes = encode(file)                        # encodes the messages of the MIDI file

    dataset_notes.extend(notes)         # 'notes_on' messages (as strings) are added to the 'dataset_notes' list
    print(f"Processed {filename}")      #  to check which file has been processed

#Print stuff for debug purposes, to be deleted once the code is definitive
with open("Input.txt", "w") as text_file:
    print(f"Note: "+str(dataset_notes), file=text_file)


#Convert midi info from strings to numbers [dataset_notes->notes_int]
for i in range(len(dataset_notes)):
    temp = re.findall(r'\d+', dataset_notes[i])     # finds all sequences of digits in each encoded note string. Used to extract numerical values from the string
    res = list(map(int, temp))                      # actual conversion of the format of the extracted digit sequences
    notes_int.append([res[1], res[2], res[3]])      # 'notes_int' contains ?pitch, velocity, and time-duration?

#Print stuff for debug purposes, to be deleted once the code is definitive
with open("Notes_int.txt", "w") as text_file:
    print(f""+str(notes_int), file=text_file)           # prints 'notes_int' value

#Midi information processing: [notes_int->notes_int_dur]
#Extracts the duration (dur) feature by evaluating after how much time the note 
#velocity is set to 0
#Removes 0 velocity messages and adds a 4th parameter: dur
for i in range(len(notes_int)-1):
    if notes_int[i][1]!=0:          # if the MIDI velocity (index[1]) is 0, it's likely the end of the note, so it skips it 
        temp=0
        for j in range(i+1, len(notes_int)):            # iteration over the group of non-zero velocity notes 
            temp+=notes_int[j][2]                       # accumulates time values into temp
            if notes_int[i][0]==notes_int[j][0] and notes_int[j][1]==0:     # until the next zero-velocity note ('notes[j][1]==0')
                notes_int[i].append(temp)               # accumulated time (temp) value as the duration of the note is added to the 'notes_int_dir' list
                notes_int_dur.append(notes_int[i])
                #adds the time interval from the 0 velocity removed message         # !! non mi è chiaro il passaggio (dal punto di vista logico)
                #to previous one in order to keep time consistency
                notes_int[j-1][2]+=notes_int[j][2]
                break
            
#Print stuff for debug purposes, to be deleted once the code is definitive
with open("Notes_int_dur.txt", "w") as text_file:
    print(f""+str(notes_int_dur), file=text_file)

#Change the range of values ('velocity', 'time' and 'duration') of notes_int_dur in order to
#higher the chance of one tuple appearing more than once 
#(i.e. making the generation less deterministic)
velocity_values = [row[1] for row in notes_int_dur]
max_velocity_value = max(velocity_values)
for row in notes_int_dur:
    row[1]=round(range_map(max_velocity_value, 0, velocity_quantization, 0, row[1]))

time_values = [row[2] for row in notes_int_dur]
max_time_value = max(time_values)
for row in notes_int_dur:
    row[2]=round(range_map(max_time_value, 0, time_quantization, 0, row[2]))

dur_values = [row[3] for row in notes_int_dur]
max_dur_value = max(dur_values)
min_dur_value = min(dur_values)
for row in notes_int_dur:
    row[3]=round(range_map(max_dur_value, min_dur_value, dur_quantization, 0, row[3]))

#Print stuff for control purposes, to be deleted once the code is definitive
with open("Notes_int_dur_ranged.txt", "w") as text_file:
    print(f""+str(notes_int_dur), file=text_file)

#Convert back to tuple as to be consistent with the following sections of code (string tuple expected later)
#Overwriting dataset_notes [notes_int_dur->a->dataset_notes]
a=[]
for i in range(len(notes_int_dur)):
    a.append(""+str(notes_int_dur[i][0])+" "+str(notes_int_dur[i][1])+" "+str(notes_int_dur[i][2])+" "+str(notes_int_dur[i][3]))
dataset_notes=a     

#Print stuff for control purposes, to be deleted once the code is definitive
with open("dataset_notes.txt", "w") as text_file:
    print(f""+str(a), file=text_file)

#set tempo, bpm and ticks per beat
first_file_midi = next(dataset_directory.iterdir())     # gets the first MIDI file in the dataset directory
with mido.MidiFile(first_file_midi) as file:            # opens the MIDI file
    tempo, bpm = setup_time(file)                       # gets tempo and bpm from the file
    ticks_per_beat = file.ticks_per_beat                # retrieves ticks per beat from the MIDI file

print(tempo, bpm, ticks_per_beat)                       # debug
tempo*=tempo_modifier                                   # to eventually adjust the tempo by the 'tempo_modifier' factor







#CHAIN GENERATION----------------------------------------------------------------------

#Chain model and matrix generation
markov_chain_notes = VariableLengthMarkovChain(max_order, dataset_notes)

# setting up of the Markov Chain using the 'VariableLengthMarkovChain' class and feeding it the dataset + max_order

#NOTES GENERATION----------------------------------------------------------------------

#Receive closeness (set_order) data
server_thread = Thread(target=run_server)
server_thread.start()           # starts the thread, running the OSC server in parallel with the program

#Run client to send generated notes
client = pyOSC3.OSCClient()     # sets up the client
client.connect( ( '127.0.0.1', 57120 ) )        # client connected on local host (on port 57120) where SuperCollider is expected to be listening for OSC messages

#Initialize starting state for the Markov Chain generation 
state_notes = tuple(dataset_notes[0:set_order])         # creating a tuple from the first 'set_order' elements of 'dataset_notes' to serve as initial state

#list containing all the generated states from which (line 121) 
#the current state is extracted based on the set_order
all_states=[]  
all_states.extend(list(state_notes))            # adds 'state_notes' to the 'all_states' list which will contain all generated states

#initialize output file to blank (file per controllare se le stringhe generate hanno senso)
with open("Output.txt", "w") as text_file:
        print(f"", file=text_file)

#Generation
while True:     # infinite loop to continuously generate new notes based on the Markov Chain model
    state_notes=tuple(all_states[(len(all_states)-set_order):len(all_states)])      # extracts the current state from the last 'set_order' elements of 'all_states'
    next_state_notes = markov_chain_notes.generate(state_notes, set_order)          # generates the next state using the Markov Chain
    all_states.append(next_state_notes)                                             # adds the generated 'next_state' to 'all_states'    

    #Print stuff for control purposes, to be deleted once the code is definitive 
    with open("Output.txt", "a") as text_file:
        print(f"Note: "+str(next_state_notes), file=text_file)
    
    #Print stuff for control purposes, to be deleted once the code is definitive
    with open("state_notes.txt", "a") as text_file:
        print(f"Note: "+str(state_notes), file=text_file)

    #divide string and extract numbers to be sent via OSC
    #values are re-ranged to their original values
    temp = re.findall(r'\d+', next_state_notes)             # finds numbers from the generated string 'netx_state_notes'
    res = list(map(int, temp))                              # string to integer conversion
    next_state_notes=res[0]                                 # note value
    next_state_velocity=range_map(velocity_quantization, 0, max_velocity_value, 0, res[1])          # note 'velocity' value extraction and re-mapping to original range
    next_state_time=range_map(time_quantization, 0, max_time_value, 0, res[2])                      # note 'time' value extraction and re-mapping to original range
    next_state_dur= mido.tick2second(range_map(dur_quantization, 0, max_dur_value, 50, res[3]), ticks_per_beat, tempo)  # note 'duration' value extraction, remapping to its original range and conversion to seconds

    #prepares the message
    msg = pyOSC3.OSCMessage()
    msg.setAddress("/numbers")              # the message containing the note will have address '/numbers'
    out=[next_state_notes, next_state_velocity, next_state_time, next_state_dur]
    msg.append(out)
    
    #computes the delta time: time interval that should pass between the last note played and the current note
    delta_time = mido.tick2second(next_state_time, ticks_per_beat, tempo)
    print(delta_time)
    time.sleep(delta_time)

    #print and send
    print(res)          # value being sent 
    print("")
    client.send(msg)
