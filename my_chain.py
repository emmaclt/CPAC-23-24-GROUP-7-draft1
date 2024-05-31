#imports: 
from collections import defaultdict  # defaultdict - dictionary subclass 
import random



#MARKOV CHAIN CLASS: it encapsulates the functionality of the variable order markov chain
class VariableLengthMarkovChain:
    # INITIALIZATION: constructor
    def __init__(self, max_order, dataset):     

        self.max_order = max_order      # maximum order of the chain
        self.dataset = dataset          # dataset used to build the markov chain
        
        #Dictionary inside dictionary: the first key is the current state to which another dictionary is linked.
        #The second dictionary has the possible outcome as key and the probability (integer number) as the linked value.
        
        self.transitions = defaultdict(lambda: defaultdict(int))         # -> used to store the transition probabilities   
        self._build_transitions()                                        # method called to build the transitions from the dataset

    def _build_transitions(self):
        #Builds the probability matrix for all orders equal or less than max_order
        for order in range(self.max_order+1):               # iteration from 0 to max_order: creates the transition probabilities matrix for all orders
            for i in range(len(self.dataset) - order):      # iteration through the dataset stopping 'order' elements before the end 
                # to ensure there are enough elements to form a state and a next state
                # this ensures that for a given order, it can construct a state of that length and determine the next state in the sequence 

                state = tuple(self.dataset[i:i+order])      # for each order, iterates though the dataset to create states and their corresponding next states
                next_state = self.dataset[i+order]          
                self.transitions[state][next_state] += 1    # updates the transition probabilities matrix dictionary with the count of transitions from each state to the next state
                                                            # this dictionary keeps track of how often each next state follows a given state
   
    def generate(self, state, set_order):
        #This for loop tries to generate the new state for the max order set for the generation (set_order)
        #if a tuple has never been encountered in the dataset (i.e. it has no probability outcome) the algorithm
        #lowers the order to be considered increasing the probability to have encountered that tuple.
        #Ultimately if the order reaches 1, the tuple is granted to be previously encountered in the dataset
        #allowing to effectively generate the next state
        if set_order>self.max_order:
            set_order=self.max_order       # ensures the set order does not exceed the max order
        
        for order in range(set_order, 0, -1):       # attempts to find the next state using decresing orders until it finds a match in the transition dictionary
            if state[(set_order-order):set_order] in self.transitions:
                choices, weights = zip(*self.transitions[state[(set_order-order):set_order]].items())
                print("Choices "+str(choices)+", weights "+str(weights))
                next_state = random.choices(choices, weights=weights)[0]        # random selection of the next state based on the weights (probabilities) of possible transitions
                
                # prints for debug
                print("Max order "+str(self.max_order)) 
                print("Set order "+str(set_order))
                print("Employed order "+str(order))
                return next_state
        raise ValueError("State not found in the Markov chain")     # if a state is not found in the markov chain: error raised

