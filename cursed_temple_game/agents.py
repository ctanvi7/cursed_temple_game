from mesa import Agent


class Explorer(Agent):
    """One human-controlled or AI-controlled temple explorer."""

    def __init__(self, model, player_number):
        super().__init__(model)
        self.player_number = player_number
        self.has_key = False
        self.has_relic = False
        self.moves = 0
        self.cost = 0
        self.finished = False
        self.finish_seconds = None
        self.trap_hits = 0
