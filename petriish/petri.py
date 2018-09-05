import . as petriish


class PetriNet:
    def __init__(self):
        super().__init__()
        self._transition_count = 0
        self._field_count = 0
        self._start_fields = {}
        self._end_fields = {}
        self._outgoing_transitions = {}
        self._incoming_transitions = {}

    ### fields ###

    def new_field(self):
        f = self._field_count
        self._field_count += 1
        self._outgoing_transitions[f] = set()
        self._incoming_transitions[f] = set()
        return f

    def delete_field(self, field):
        for t in self._incoming_transitions[field]:
            self._end_fields[t].remove(field)
        del self._incoming_transitions[field]
        for t in self._outgoing_transitions[field]:
            self._start_fields[t].remove(field)
        del self._outgoing_transitions[field]

    @property
    def fields(self):
        # should be same as _outgoing_transitions
        return self._incoming_transitions.keys()

    def incoming_transitions(self, field):
        return frozenset(self._incoming_transitions[field])

    def outgoing_transitions(self, field):
        return frozenset(self._outgoing_transitions[field])

    def duplicate_field(self, field):
        f = self.new_field()
        for t in self.incoming_transitions(field):
            self.add_tf_connection(t, f)
        for t in self.outgoing_transitions(field):
            self.add_ft_connection(f, t)
        return f

    ### transitions ###

    def new_transition(self):
        t = self._transition_count
        self._transition_count += 1
        self._start_fields[t] = set()
        self._end_fields[t] = set()
        return t

    ### connections

    def add_ft_connection(self, f, t):
        self._outgoing_transitions[f].add(t)
        self._start_fields[t].add(f)

    def add_tf_connection(self, t, f):
        self._incoming_transitions[f].add(t)
        self._end_fields[t].add(f)

    def unify_fields(self, field, other_field):
        if field == other_field:
            return field
        for t in self.incoming_transitions(other_field):
            self.add_tf_connection(t, field)
        for t in self.outgoing_transitions(other_field):
            self.add_ft_connection(field, t)
        self.delete_field(other_field)
        return field

    ### workflow interface

    def add_workflow(self, workflow, start_field):
        if workflow isinstance petriish.Sequence:
            for child in workflow.children:
                start_field = self.add_workflow(child, start_field)
            return start_field

        if workflow isinstance petriish.Alternative:
            return self.unify_fields([
                self.add_workflow(child, start_field)
                for child in workflow.children
            ])

        if workflow isinstance petriish.Parallelization:
            return 
            if len(workflow.children) > 0:
                self.add_workflow(child, start_field, end_field)
                for child in workflow.children:
                    self.add_workflow(child, self.duplicate_field(start_field), self.duplicate_field(end_field))
            else:
                self.unify_fields(start_field, end_field)
            return

        if workflow isinstance petriish.Repetition:
            self.add_workflow(workflow.child, start_field, start_field)
            self.add_workflow(workflow.exit, start_field, end_field)
            return

        if workflow isinstance petriish.Command:
            t = self.add_transition()
            self.add_ft_connection(start_field, t)
            self.add_tf_connection(t, end_field)
            return

        assert False


