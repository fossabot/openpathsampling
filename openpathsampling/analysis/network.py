import openpathsampling as paths

class TransitionNetwork(object):
    def __init__(self):
        pass

    @property
    def all_ensembles(self):
        pass

#    def replica_exchange_matrix(self):

class TISNetwork(TransitionNetwork):
    # TODO: most of the analysis stuff should end up in here; the bigger
    # differences are in setup, not analysis
    def __init__(self):
        # this should check to build the replica exchange network. If the
        # number of neighbors at any station is more than 2, we can't do
        # "normal" replica flow -- instead produce a network graph. Or,
        # actually, ALWAYS produce a network graph (although this will be a
        # feature to implement later)
        pass

    def from_transitions(self, transitions, interfaces=None):
        # this will have to be disabled until I can do something
        # better with it
        pass


#def join_mis_minus(minuses):
    #pass

#def msouter_state_switching(mstis, storage):

def get_movers_from_transitions(label, transitions):
    movers = []
    for trans in transitions:
        movers += trans.movers[label]
    return movers

class MSTISNetwork(TISNetwork):
    """
    Multiple state transition interface sampling network.

    The way this works is that it sees two effective sets of transitions.
    First, there are sampling transitions. These are based on ensembles
    which go to any final state. Second, there are analysis transitions.
    These are based on ensembles which go to a specific final state.
    """
    def __init__(self, trans_info):
        self.trans_info = trans_info
        if not hasattr(self, "from_state"):
            self.from_state = {}
            self.outer_ensembles = []
            self.outers = []
            self.build_from_state_transitions(trans_info)

        # get the movers from all of our sampling-based transitions
        if not hasattr(self, "movers"):
            self.movers = { }
            self.build_movers()

        # TODO: add building of analysis transitions (not to be saved)


#    def disallow(self, stateA, stateB):

    def build_from_state_transitions(self, trans_info):
        states, interfaces, names, orderparams = zip(*trans_info)
        all_states = paths.volume.join_volumes(states)
        all_states.name = "all states"
        for (state, ifaces, name, op) in trans_info:
            state_index = states.index(state)
            state.name = name
            other_states = states[:state_index]+states[state_index+1:]
            union_others = paths.volume.join_volumes(other_states)
            union_others.name = "all states except " + str(name)

            self.from_state[state] = paths.RETISTransition(
                stateA=state, 
                stateB=union_others,
                interfaces=ifaces[:-1],
                name="Out "+name,
                orderparameter=op
            )
            self.outers.append(ifaces[-1])
            outer_ensemble = paths.TISEnsemble(
                initial_states=state,
                final_states=all_states,
                interface=ifaces[-1]
            )
            outer_ensemble.name = "outer " + str(state)
            self.outer_ensembles.append(outer_ensemble)


    def build_movers(self):
        for label in ['shooting', 'pathreversal', 'minus', 'repex']:
            self.movers[label] = get_movers_from_transitions(
                label=label,
                transitions=self.from_state.values()
            )
        # default is only 1 MS outer, but in principle you could have
        # multiple distinct MS outer interfaces
        self.ms_outers = [paths.ensemble.join_ensembles(self.outer_ensembles)]
        self.movers['msouter_repex'] = [
            paths.ReplicaExchangeMover(
                ensembles=[trans.ensembles[-1], self.ms_outers[0]]
            )
            for trans in self.from_state.values()
        ]
        self.movers['msouter_pathreversal'] = [
            paths.PathReversalMover(
                ensembles=[self.ms_outers[0]]
            )
        ]
        self.movers['msouter_shooting'] = [
            paths.OneWayShootingMover(
                selector=paths.UniformSelector(),
                ensembles=[self.ms_outers[0]]
            )
        ]

        shooting_chooser = paths.RandomChoiceMover(
            movers=self.movers['shooting'] + self.movers['msouter_shooting'],
            name="ShootingChooser"
        )
        repex_chooser = paths.RandomChoiceMover(
            movers=self.movers['repex'],
            name="RepExChooser"
        )
        rev_chooser = paths.RandomChoiceMover(
            movers=(self.movers['pathreversal'] + 
                    self.movers['msouter_pathreversal']),
            name="ReversalChooser"
        )
        minus_chooser = paths.RandomChoiceMover(
            movers=self.movers['minus'],
            name="MinusChooser"
        )
        msouter_chooser = paths.RandomChoiceMover(
            movers=self.movers['msouter_repex'],
            name="MSOuterRepexChooser"
        )
        weights = [
            len(shooting_chooser.movers),
            len(repex_chooser.movers) / 2,
            len(rev_chooser.movers) / 2,
            0.2 / len(shooting_chooser.movers),
            len(self.outer_ensembles)
        ]
        root_mover = paths.RandomChoiceMover(
            movers=[shooting_chooser, repex_chooser, rev_chooser,
                    minus_chooser, msouter_chooser],
            weights=weights
        )


    def default_movers(self):
        pass

    def rate_matrix(self, storage):
        pass


#def multiple_set_minus_switching(mistis, storage):

class MISTISNetwork(TISNetwork):
    def __init__(self, transitions):
        pass


    def default_movers(self):
        pass

