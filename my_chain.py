from collections import defaultdict
import random




class VariableLengthMarkovChain:
    def __init__(self, max_order, dataset):
        self.max_order = max_order
        self.dataset = dataset
        self.transitions = defaultdict(lambda: defaultdict(int))
        self._build_transitions()

    def _build_transitions(self):
        for order in range(self.max_order+1):
            for i in range(len(self.dataset) - order):
                state = tuple(self.dataset[i:i+order])
                next_state = self.dataset[i+order]
                self.transitions[state][next_state] += 1

    def generate(self, state, set_order):
        for order in range(set_order, 0, -1):
            if state[:order] in self.transitions:
                choices, weights = zip(*self.transitions[state[:order]].items())
                next_state = random.choices(choices, weights=weights)[0]
                print(order)
                return next_state
        raise ValueError("State not found in the Markov chain")







#INITIALIZE
dataset = [1, 2, 3, 4, 5, 3, 3, 2, 4, 1, 1, 2, 3, 5, 4, 2, 3, 3, 1, 5, 3, 2, 1, 1, 3, 5, 3, 5, 2, 3, 1, 5, 4, 3, 2, 1, 5, 5, 3, 3]
max_order = 8
set_order = 4
markov_chain = VariableLengthMarkovChain(max_order, dataset)
#print(markov_chain.transitions)


#GENERATE
state = tuple(dataset[0:max_order])
for i in range(60):
    next_state = markov_chain.generate(state, set_order)
    print("Next state after", state, ":", next_state)
    update_state=list(state)
    update_state.pop(0)
    update_state.append(next_state)
    state=tuple(update_state)

