
import numpy as np
import heapq

class HMM:

    def __init__(self, mazefile, coloring = True, num_states = 16):

        if coloring:
            print("Display shows estimated probabilities at each map space.")
            print("The white probability shows the true location of the robot.")
            self.coloring = True
        else:
            print("Display shows estimated probabilities at each map space.")
            print("'*' shows the true location of the robot. Estimated probability"
                + " at that location shown below map.")
            self.coloring = False

        self.num_states = num_states
        self.prior = np.full((self.num_states, 1) , 1/self.num_states);
        self.priors = [self.prior]
        self.smoothed = None

        self.transition_probs = {}

        self.walls = set()

        self.color = []

        self.colortable = {}
        self.colortable['r'] = 0
        self.colortable['g'] = 1
        self.colortable['b'] = 2
        self.colortable['y'] = 3
        self.colortable[0] = 'r'
        self.colortable[1] = 'g'
        self.colortable[2] = 'b'
        self.colortable[3] = 'y'

        self.bad_reading_rate = .04
        self.good_reading_rate = .88

        self.parse_maze(mazefile)
        self.set_transition_probs()

    def parse_maze(self, mazefile):
        maze = open(mazefile, 'r')
        i = 0
        for line in maze:
            for item in line:
                if item == '\n':
                    continue
                if item == '#':
                    self.walls.add(i)
                    self.color.append(-1)
                    i += 1
                    continue
                color = self.colortable[item]
                self.color.append(color)
                i += 1

    # Sets dictionary of transition probability lists for each state
    def set_transition_probs(self):

        for i in range(self.num_states):
            probabilities = np.zeros((self.num_states, 1))
            transitions = []
            if i % 4 != 0: # Not left edge of maze
                transitions.append(-1)
            if (i+1) % 4 != 0: # Not right edge of maze
                transitions.append(1)
            if i > 3: # Not top edge of maze
                transitions.append(-4)
            if i < 12: # Not bottom edge of maze
                transitions.append(4)

            for move in transitions:
                if i + move not in self.walls: # It moved!
                    probabilities[i + move] = .25
                else: # It hit a wall and stayed where it was!
                    probabilities[i] += .25
            for j in range(4 - len(transitions)):
                probabilities[i] += .25

            self.transition_probs[i] = probabilities


    def filter(self, readings, rlocs):
        # Project current state forward
        evprob = self.get_evidence_prob(readings[0])
        self.prior = self.prior * evprob

        self.normalize()

        print("Forward pass:")
        self.disp_state(rlocs[0])

        for i in range(1, len(readings)):
            self.priors.append(self.prior)
            self.move_state()

            evprob = self.get_evidence_prob(readings[i])
            self.prior = self.prior * evprob

            self.normalize()
            #self.top_states(3)
            self.disp_state(rlocs[i])
        self.priors.append(self.prior)

        self.smooth(readings, rlocs)

        return self.top_states(1, disp=False)[0]


    # Returns the probabilities of the given reading at each square
    def get_evidence_prob(self, evidence):
        distribution = np.zeros((self.num_states, 1))

        for state in range(self.num_states):
            if self.color[state] == evidence:
                distribution[state] = self.good_reading_rate
            else:
                distribution[state] = self.bad_reading_rate
        return distribution

    # Updates posterior based on the fact that the robot will move in a random
    # direction
    def move_state(self):

        new_prior = np.zeros((self.num_states, 1));

        for i in range(self.num_states):
            # For every state, multiply likelihood of that state (prior)
            # by the likelihood of transitioning to other states
            new_prior += self.transition_probs[i] * self.prior[i]
        self.prior = new_prior

    # Display the n top states
    def top_states(self, n, disp = True):
        top_n_states = []
        state_queue = []
        for i in range(len(self.prior)):
            heapq.heappush(state_queue, (-self.prior[i], i))

        if disp:
            print("Displaying the top " + str(n) + " posterior probabilities:")
        for i in range(n):
            if state_queue:
                stn = heapq.heappop(state_queue)
                st = (-stn[0], stn[1])
                top_n_states.append(st)
                if disp:
                    color = st[1]
                    print("Color: " + str(color) + " with probability " + str(st[0]))
            else: # queue is empty
                break

        return top_n_states

    def normalize(self):
        priorsum = np.sum(self.prior)
        self.prior /= priorsum

    def smooth(self, readings, rlocs):
        print("================")
        print("Backwards Pass")
        print("================")
        self.smoothed = [None] * (len(readings) + 1)
        self.smoothed[len(readings)] = np.ones((self.num_states, 1))

        for i in range(len(readings) - 1, -1, -1):
            forward_prob = self.priors[i+1]
            self.get_back_prob(i, readings[i])
            self.smoothed[i] = forward_prob * self.smoothed[i]
            self.smoothed[i] /= np.sum(self.smoothed[i])

        for i in range(len(readings)):
            self.disp_state(rlocs[i], state=self.smoothed[i])

    # Sets backwards probabilities
    def get_back_prob(self, i, reading):

        base_prob = np.zeros((self.num_states, 1))
        basis = self.get_evidence_prob(reading) * self.smoothed[i+1]

        for j in range(self.num_states):
            base_prob += basis[j] * self.transition_probs[j]

        self.smoothed[i] = base_prob

    # Displays a distribution (by default the current distribution)
    def disp_state(self, rloc, state = None):
        if state is None:
            state = self.prior
        if self.coloring:
            try:
                from termcolor import colored
            except:
                print("Error importing termcolor module. Continuing without color.")
                self.coloring = False
        trueProb = ""
        n_rows = 4
        n_cols = 4
        print("+++++++++++++++")
        for i in range(n_rows):
            for j in range(n_cols):
                prior = state[n_cols*i + j]
                itemstr = "%.1f" % prior
                if self.coloring:
                    item = colored(itemstr, 'blue')
                    if prior >= .1:
                        item = colored(itemstr, 'red')
                    if prior >= .3:
                        item = colored(itemstr, 'yellow')
                    if n_cols*i + j == rloc:
                        item = colored(itemstr, 'white')
                else:
                    item = itemstr
                    if n_cols*i + j == rloc:
                        item = ' * '
                        trueProb = itemstr
                if n_cols*i + j in self.walls:
                    item = '###'

                print(item, end = ' ')

            print(' ')
        print("+++++++++++++++")
        if not self.coloring:
            print("Estimated probability of true location is " + trueProb)
        print(' ')
