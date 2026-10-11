"""A* over (position, has_key, has_relic). No hard-coded route."""
import heapq
from itertools import count


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def heuristic(model, state):
    position, key, relic = state
    if relic:
        return distance(position, model.start)
    if key:
        return distance(position, model.relic)
    return (distance(position, model.key) +
            distance(model.key, model.relic) +
            distance(model.relic, model.start))


def astar(model, explorer):
    """Return (path of coordinates, expanded states); costs are at least 1."""
    initial = (explorer.pos, explorer.has_key, explorer.has_relic)
    serial = count()
    frontier = [(heuristic(model, initial), 0, next(serial), initial)]
    best = {initial: 0}
    parent = {}
    expanded = 0
    while frontier:
        _, cost, _, state = heapq.heappop(frontier)
        if cost != best[state]:
            continue
        expanded += 1
        pos, key, relic = state
        if pos == model.start and relic:
            route = []
            while state != initial:
                route.append(state[0])
                state = parent[state]
            route.reverse()
            return route, expanded
        for new_pos in model.neighbors(pos, key):
            next_key = key or new_pos == model.key
            next_relic = relic or (new_pos == model.relic and next_key)
            next_state = (new_pos, next_key, next_relic)
            # Moving hazards are dynamic. This is the current snapshot;
            # AI replans after each turn, so it can respond to hazard motion.
            new_cost = cost + model.tile_cost(new_pos)
            if new_cost < best.get(next_state, float('inf')):
                best[next_state] = new_cost
                parent[next_state] = state
                heapq.heappush(frontier, (new_cost + heuristic(model, next_state),
                                          new_cost, next(serial), next_state))
    return [], expanded
