# Archaeologist's Cursed Temple

A turn-based exploration game built with **Mesa 3.5.1**, **Solara**, and **A\* informed search**. Supports 1–4 local players, an optional timer, three difficulty levels, different map sizes, stationary obstacles, weighted traps, moving hazards, and AI navigation.

## Run on Windows (Python 3.12)

Open this folder in VS Code, then in its **PowerShell** terminal:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m solara run app.py
```

Open the local URL displayed in the terminal (usually http://localhost:8765).

**Do not run `python app.py`.** Solara hosts the UI.

## How to play

1. Choose map size, difficulty, number of players (1–4), and timer. Click **Create / restart temple**.
2. Select **Human** to move with on-screen directional buttons. In multiplayer, click **Pass turn** to rotate between explorers.
3. Find the key on the left side, cross the central gate, collect the relic on the right side, and return to the entrance.
4. Select **AI** to plan with A*. Click **Find route**, then **Run** or **Next step**. Pause/resume or adjust the speed.
5. The map stays solvable and the gate cannot be bypassed. Moving traps change location after every valid move. A* replans after each step.

## AI details

- **State:** `(position, has_key, has_relic)`.
- **Actions:** four cardinal moves.
- **Goal:** return to the entrance with the relic.
- **Evaluation:** `f(n) = g(n) + h(n)`.
- **Costs:** normal tile 1, mud 3, fixed trap 5. A moving hazard adds a 5-point penalty on collision.
- **Heuristic:** Manhattan distances through the outstanding objectives (key → relic → entrance), which is admissible for positive movement costs.
- **Dynamic hazards:** A* optimizes for a snapshot of terrain and replans after each turn; it does **not** predict future hazard positions.

## PEAS

- **Performance:** recover the relic, escape, minimize movement cost, avoid hazards, finish before the optional timer.
- **Environment:** grid temple with walls, gate, key, relic, mud, fixed traps and moving traps.
- **Actuators:** up, down, left, right.
- **Sensors:** full map, agent position, inventory, and current hazard locations.

## Notes

This version uses a simple Solara tile-board and timed, tile-by-tile AI movement. The board is styled with subtle CSS transitions, but the explorer does **not** use continuous sprite interpolation between cells. Multiplayer is local turn-based, not networked. Solara and Mesa must be installed in the **same** Python interpreter.
