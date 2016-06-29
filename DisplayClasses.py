
class Display(object):
    """
    This class represents a display -- it has properties that specify its width and number of lines.
    It also has a property that represents its current state (e.g. what it is currently displaying).
    It has an update method which is fed a display object, a transition function and a delay.
    The transition function takes in a current display state and a desired display state, then returns
    a list of intermediate display states that need to be transitioned through.

    A display state is stored as a list of length num_lines that contains only strings of length num_chars.
    """
    def __init__(self, num_lines, num_chars):
        self.num_lines = num_lines
        self.num_chars = num_chars
        self.currentstate = [' '*num_chars]*num_lines

    def determine_transition(self, transitionfunction, messageobject):
        messageobject.update(num_lines=self.num_lines, num_chars=self.num_chars)
        return transitionfunction(self.currentstate, messageobject.get_message())

    def update(self,transitionfunction,messageobject):
        # this will be different for each display type, so must be overridden
        raise NotImplementedError


class SimpleDisplay(Display):
    """
    This class is the simplest display possible - it just prints the info to the console.
    """
    def __init__self(self,num_lines,num_chars):
        Display.__init__(self,num_lines,num_chars)
    def update(self,transitionfunction,messageobject):
        states = self.determine_transition(transitionfunction, messageobject)
        for i in range(len(states)):
            print(states[i])


def SimpleTransition(current_state,desired_state):
    """
    The simplest possible transition -- go to the desired state directly with no fancy stuff.
    :param current_state: the current display state -- ignored by this function but included for consistency with other
    transition functions.
    :param desired_state: the desired display state
    :return: in this case, just a single-element list containing the desired state
    """
    return [desired_state]