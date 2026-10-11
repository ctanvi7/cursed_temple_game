"""Mesa temple model; turn-based players and moving hazards."""
import random
import time
from mesa import Model
from mesa.space import MultiGrid
from agents import Explorer


class TempleModel(Model):
    def __init__(self, size=11, players=1, difficulty='Normal', timer_limit=0, seed=42):
        super().__init__(seed=seed)
        self.width = self.height = int(size)
        self.grid = MultiGrid(self.width, self.height, torus=False)
        self.start = (1, 1)
        self.key = (2, self.height - 3)
        self.relic = (self.width - 3, self.height - 3)
        self.gate = (self.width // 2, self.height // 2)
        self.difficulty = difficulty
        self.timer_limit = int(timer_limit)
        self.started_at = time.monotonic()
        self.paused_at = None
        self.paused_total = 0.0
        self.timed_out = False
        self.turn = 0
        self.active_index = 0
        self.message = 'Find the key, cross the gate, recover the relic, and escape.'
        self.explored = 0
        self.route = []
        self.route_owner = None
        self.walls = set()
        self.mud = set()
        self.traps = set()
        self.hazards = []
        self._build_map(seed)
        self.players = []
        for i in range(max(1, min(4, int(players)))):
            agent = Explorer(self, i + 1)
            self.grid.place_agent(agent, self.start)
            self.players.append(agent)

    def _build_map(self, seed):
        rng = random.Random(seed + self.width * 19 + len(self.difficulty))
        n = self.width
        # Outer walls and a full-height internal barrier. The only crossing
        # is the locked gate: key possession is genuinely necessary.
        for x in range(n):
            self.walls.add((x, 0))
            self.walls.add((x, n - 1))
        for y in range(n):
            self.walls.add((0, y))
            self.walls.add((n - 1, y))
        middle = n // 2
        for y in range(1, n - 1):
            if y != middle:
                self.walls.add((middle, y))
        protected = {self.start, self.key, self.relic, self.gate}
        # Ensure corridors leading to gate remain open on both sides.
        protected.update({(middle - 1, middle), (middle + 1, middle)})
        candidates = [(x, y) for x in range(1, n - 1) for y in range(1, n - 1)
                      if (x, y) not in self.walls | protected]
        rng.shuffle(candidates)
        wall_target = {'Easy': 5, 'Normal': 11, 'Hard': 17}[self.difficulty] * (n*n) // 121
        # Only accept obstacles when all key segments remain reachable.
        for tile in candidates:
            if wall_target <= 0:
                break
            self.walls.add(tile)
            if (not self._reachable(self.start, self.key, False) or
                    not self._reachable(self.key, self.relic, True) or
                    not self._reachable(self.relic, self.start, True)):
                self.walls.remove(tile)
            else:
                wall_target -= 1
        floor = [p for p in candidates if p not in self.walls]
        rng.shuffle(floor)
        count = {'Easy': 4, 'Normal': 8, 'Hard': 13}[self.difficulty] * (n*n) // 121
        self.traps = set(floor[:count])
        self.mud = set(floor[count:count + count])
        # Hazards are independent of fixed traps and move after each valid turn.
        hazard_count = {'Easy': 1, 'Normal': 2, 'Hard': 4}[self.difficulty]
        spots = [p for p in floor if p not in self.traps | self.mud]
        self.hazards = spots[:hazard_count]

    def _reachable(self, start, goal, has_key):
        todo, seen = [start], {start}
        for current in todo:
            if current == goal:
                return True
            for nxt in self.neighbors(current, has_key):
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return False

    def neighbors(self, pos, has_key):
        x, y = pos
        for nxt in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
            if not (0 <= nxt[0] < self.width and 0 <= nxt[1] < self.height):
                continue
            if nxt in self.walls or (nxt == self.gate and not has_key):
                continue
            yield nxt

    def tile_cost(self, pos):
        return 5 if pos in self.traps else 3 if pos in self.mud else 1

    @property
    def active(self):
        return self.players[self.active_index]

    def elapsed(self):
        until = self.paused_at if self.paused_at is not None else time.monotonic()
        return max(0, int(until - self.started_at - self.paused_total))

    def remaining(self):
        return max(0, self.timer_limit - self.elapsed()) if self.timer_limit else None

    def check_timer(self):
        if self.timer_limit and self.remaining() == 0:
            self.timed_out = True
            self.message = 'Time is up! Restart to try again.'
        return self.timed_out

    def pause(self):
        if self.paused_at is None:
            self.paused_at = time.monotonic()
        else:
            self.paused_total += time.monotonic() - self.paused_at
            self.paused_at = None

    def move(self, dx, dy):
        if self.check_timer() or self.paused_at is not None:
            return False
        player = self.active
        if player.finished:
            self.message = 'This explorer has already escaped.'
            return False
        dest = (player.pos[0] + dx, player.pos[1] + dy)
        if dest not in self.neighbors(player.pos, player.has_key):
            self.message = 'Blocked by stone or a locked gate.'
            return False
        self.grid.move_agent(player, dest)
        player.moves += 1
        player.cost += self.tile_cost(dest)
        self.turn += 1
        event = ''
        if dest == self.key and not player.has_key:
            player.has_key = True
            event = 'Ancient key collected! '
        if dest == self.relic and player.has_key and not player.has_relic:
            player.has_relic = True
            event += 'Sacred relic recovered! '
        if dest in self.traps:
            player.trap_hits += 1
            event += 'Spike trap! '
        self._move_hazards()
        if dest in self.hazards:
            player.cost += 5
            player.trap_hits += 1
            event += 'Moving trap struck! +5 cost. '
        if dest == self.start and player.has_relic:
            player.finished = True
            player.finish_seconds = self.elapsed()
            event += f'Explorer {player.player_number} escaped! '
        self.message = event or 'Keep exploring the temple.'
        return True

    def _move_hazards(self):
        updated = []
        for index, hazard in enumerate(self.hazards):
            options = [hazard] + [p for p in self.neighbors(hazard, True)
                                  if p not in {self.start, self.key, self.relic, self.gate}]
            # Deterministic per turn, so demos are reproducible.
            chosen = random.Random(self.turn * 997 + index * 53).choice(options)
            updated.append(chosen)
        self.hazards = updated

    def next_player(self):
        if len(self.players) < 2:
            return
        for _ in self.players:
            self.active_index = (self.active_index + 1) % len(self.players)
            if not self.active.finished:
                break
        self.route = []
        self.route_owner = None
        self.message = f'Explorer {self.active.player_number}: your turn.'
