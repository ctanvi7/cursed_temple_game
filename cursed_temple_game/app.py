"""Solara web UI. Run with ``python -m solara run app.py``."""
import solara
from model import TempleModel
from search import astar


CSS = """
html, body, #root, #app, .solara-app, .solara-app-main, .v-application, .v-application__wrap,
main, .v-main, .v-container, .solara-content, .solara-app-container,
.v-sheet, .v-card, .v-card-text, .v-card-title, .v-card-actions, .v-toolbar,
.v-footer, .v-main__wrap, .v-responsive { background-color: #12130f !important; color: #f4e7c5 !important; }
html, body, #root, #app, .v-application, .v-application__wrap { min-height: 100% !important; }
body { background: radial-gradient(ellipse at 50% 0%, #30291d 0%, #191a15 52%, #10110e 100%) fixed !important; }
.temple-app { width: 100%; max-width: none; min-height: 100vh; box-sizing: border-box; margin: 0; padding: clamp(12px, 2vw, 28px); color: #f4e7c5 !important; font-family: Georgia, 'Trebuchet MS', serif; background: transparent !important; }
.temple-hero { padding: 24px 30px; border: 1px solid #9b784a; border-radius: 18px; background: linear-gradient(115deg, #51402a, #292b22 65%, #413326); box-shadow: 0 10px 30px #0009; }
.temple-title { margin: 3px 0; font-size: clamp(32px, 4vw, 48px); line-height: 1.12; font-weight: 900; color: #ffe4a1 !important; text-shadow: 0 2px #5d3925; }
.temple-subtitle { color: #e5d4ae !important; font-size: 17px; }
.temple-card { padding: 20px; border: 1px solid #5c5844; border-radius: 16px; background: #24251f !important; color: #f4e7c5 !important; box-shadow: 0 8px 24px #0008; }
.temple-card h3 { color: #f0bd64 !important; margin: 0 0 14px; font-size: 22px; }
.temple-card p, .temple-card strong { color: #f4e7c5 !important; }
.temple-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.setup-label { color: #d6c298 !important; font-size: 13px; font-weight: 700; margin: 8px 0 3px; }
.setup-group .v-btn { border: 1px solid #766b50 !important; color: #f4e7c5 !important; background: #39382e !important; }
.setup-group .v-btn--active { background: #a97535 !important; color: #fff2d0 !important; }
.temple-board { display: flex; flex-direction: column; gap: 6px; width: max-content; max-width: 100%; padding: 12px; border: 1px solid #796645; border-radius: 14px; background: #171915 !important; box-shadow: inset 0 0 28px #0009; }
.temple-board-row { display: flex; gap: 6px; }
.temple-tile { width: clamp(48px, 5vw, 66px) !important; height: clamp(48px, 5vw, 66px) !important; min-width: clamp(48px, 5vw, 66px) !important; padding: 0 !important; margin: 0 !important; border: 2px solid #77705d !important; border-radius: 12px !important; font-family: 'Segoe UI Symbol', 'DejaVu Sans', sans-serif !important; font-size: clamp(25px, 2.4vw, 34px) !important; font-weight: 700 !important; color: #fff4d6 !important; text-shadow: 0 2px 3px #000b; box-shadow: inset 0 2px #ffffff22, 0 3px 6px #0008; }
.temple-tile .v-btn__content { white-space: normal !important; line-height: 1 !important; }
.temple-stat { padding: 14px; border: 1px solid #625a43; border-radius: 12px; background: #323127 !important; }
.temple-stat strong { display: block; color: #ffce73 !important; font-size: 24px; }
.temple-stat span { color: #e8dcc0 !important; font-size: 14px; }
.objective { padding: 14px; border: 1px solid #a17d4b; border-radius: 12px; background: #393329 !important; color: #ffe6ae !important; font-size: 20px; font-weight: 800; }
.move-button { min-width: 116px !important; height: 54px !important; font-size: 16px !important; font-weight: 800 !important; }
.temple-card .v-btn { color: #fff2d0 !important; }
.temple-card .v-label, .temple-card .v-field__input, .temple-card .v-select__selection-text, .temple-card .v-field__outline { color: #fff0cb !important; opacity: 1 !important; }
.temple-card .v-field, .temple-card .v-input__control { background: #35352c !important; color: #fff0cb !important; border-radius: 9px; }
.v-main, .v-container, .solara-content, .solara-app-container { max-width: none !important; width: 100% !important; }
.v-btn { transition: transform .15s ease, filter .15s ease !important; }
.v-btn:hover { transform: translateY(-1px); filter: brightness(1.12); }
@media (max-width: 760px) { .temple-app { padding: 10px; } .temple-hero { padding: 18px; } .temple-tile { width: clamp(29px, 7.7vw, 45px) !important; height: clamp(29px, 7.7vw, 45px) !important; min-width: clamp(29px, 7.7vw, 45px) !important; font-size: 23px !important; } .temple-board, .temple-board-row { gap: 3px; } }
@media (prefers-reduced-motion: reduce) { .v-btn { transition: none !important; } }
"""


def tile_info(game, pos, route, active):
    """Return a Unicode icon, temple tile color, and accessible tooltip."""
    if pos == active.pos:
        return "\u265f", "#d89b35", f"Explorer {active.player_number}"
    other = next((p for p in game.players if p is not active and p.pos == pos), None)
    if other:
        return "\u265e", "#3c91a1", f"Explorer {other.player_number}"
    if pos in game.walls:
        return "", "#282d2d", "Stone wall"
    if pos == game.gate:
        return ("\u2726" if active.has_key else "\u25a4"), "#9a7041", "Open gate" if active.has_key else "Locked stone gate"
    if pos == game.key and not active.has_key:
        return "\u2694", "#d5a72e", "Ancient key"
    if pos == game.relic and not active.has_relic:
        return "\u25c6", "#36a6b3", "Sacred relic"
    if pos == game.start:
        return "\u2302", "#638657", "Entrance and exit"
    if pos in game.hazards:
        return "\u2620", "#a84f49", "Moving hazard"
    if pos in game.traps:
        return "\u26a0", "#b64f3c", "Spike trap"
    if pos in game.mud:
        return "\u2248", "#806342", "Slow mud"
    if pos in route:
        return "\u2022", "#68834c", "Planned route"
    return "\u00b7", "#454943", "Stone floor"


@solara.component
def Page():
    solara.Style(CSS)
    size, set_size = solara.use_state(11)
    difficulty, set_difficulty = solara.use_state("Normal")
    player_count, set_player_count = solara.use_state(1)
    timer_choice, set_timer_choice = solara.use_state("Off")
    game, set_game = solara.use_state(TempleModel())
    mode, set_mode = solara.use_state("Human")
    running, set_running = solara.use_state(False)
    speed, set_speed = solara.use_state("Normal")
    refresh, set_refresh = solara.use_state(0)
    show_help, set_show_help = solara.use_state(False)

    def redraw():
        set_refresh(lambda value: value + 1)

    def stop_ai():
        set_running(False)

    def new_game():
        stop_ai()
        minutes = {"Off": 0, "2 min": 120, "5 min": 300, "10 min": 600}[timer_choice]
        set_game(TempleModel(size=size, players=player_count,
                             difficulty=difficulty, timer_limit=minutes))
        redraw()

    def human_move(dx, dy):
        stop_ai()
        if game.move(dx, dy):
            game.route = []
            game.route_owner = None
        redraw()

    def plan():
        stop_ai()
        game.route, game.explored = astar(game, game.active)
        game.route_owner = game.active.player_number
        game.message = (f"A* planned {len(game.route)} steps." if game.route
                        else "No route found. Check your position and try again.")
        redraw()

    def next_ai_step():
        if not game.route or game.check_timer() or game.paused_at is not None:
            stop_ai()
            redraw()
            return
        target = game.route.pop(0)
        x, y = game.active.pos
        if not game.move(target[0] - x, target[1] - y):
            stop_ai()
            game.route = []
            game.message = "The route changed. Find a new route to continue."
        elif not game.active.finished:
            game.route, game.explored = astar(game, game.active)
        else:
            stop_ai()
        redraw()

    async def run_ai():
        import asyncio

        while running:
            await asyncio.sleep({"Slow": 0.7, "Normal": 0.35, "Fast": 0.16}[speed])
            if game.check_timer():
                stop_ai()
                redraw()
                return
            next_ai_step()
            if not game.route or game.active.finished or game.timed_out:
                stop_ai()
                redraw()
                return

    solara.lab.use_task(run_ai, dependencies=[running, game, speed])
    _ = refresh
    player = game.active
    can_move = not player.finished and not game.timed_out and game.paused_at is None

    with solara.Column(gap="18px", classes=["temple-app"]):
        with solara.Div(classes=["temple-hero"]):
            solara.HTML(tag="div", unsafe_innerHTML="THE LOST EXPEDITION &nbsp;·&nbsp; FIELD JOURNAL 01", classes=["temple-kicker"])
            solara.HTML(tag="div", unsafe_innerHTML="Archaeologist’s Cursed Temple", classes=["temple-title"])
            solara.HTML(tag="div", unsafe_innerHTML="Find the key. Claim the relic. Escape the temple.", classes=["temple-subtitle"])

        with solara.Div(classes=["temple-card"]):
            solara.Markdown("### New game")
            with solara.Row(gap="18px", style={"flex-wrap": "wrap"}):
                with solara.Column(gap="3px"):
                    solara.HTML(tag="div", unsafe_innerHTML="PLAY", classes=["setup-label"])
                    solara.ToggleButtonsSingle(value=mode, values=["Human", "AI"], on_value=lambda value: (stop_ai(), set_mode(value)), classes=["setup-group"], dense=True)
                with solara.Column(gap="3px"):
                    solara.HTML(tag="div", unsafe_innerHTML="DIFFICULTY", classes=["setup-label"])
                    solara.ToggleButtonsSingle(value=difficulty, values=["Easy", "Normal", "Hard"], on_value=set_difficulty, classes=["setup-group"], dense=True)
                with solara.Column(gap="3px"):
                    solara.HTML(tag="div", unsafe_innerHTML="MAP", classes=["setup-label"])
                    solara.ToggleButtonsSingle(value=size, values=[9, 11, 13], on_value=set_size, classes=["setup-group"], dense=True)
                with solara.Column(gap="3px"):
                    solara.HTML(tag="div", unsafe_innerHTML="PLAYERS", classes=["setup-label"])
                    solara.ToggleButtonsSingle(value=player_count, values=[1, 2, 3, 4], on_value=set_player_count, classes=["setup-group"], dense=True)
                with solara.Column(gap="3px"):
                    solara.HTML(tag="div", unsafe_innerHTML="TIMER", classes=["setup-label"])
                    solara.ToggleButtonsSingle(value=timer_choice, values=["Off", "2 min", "5 min"], on_value=set_timer_choice, classes=["setup-group"], dense=True)
                solara.Button("START EXPEDITION", on_click=new_game, color="#b574ff")

        with solara.Row(gap="18px", style={"align-items": "flex-start", "flex-wrap": "wrap", "width": "100%"}):
            with solara.Column(gap="12px", style={"flex": "1 1 720px", "min-width": "0"}):
                with solara.Div(classes=["temple-card"]):
                    solara.Markdown("### Temple map")
                    with solara.Div(classes=["temple-board"]):
                        for y in reversed(range(game.height)):
                            with solara.Row(gap="4px", classes=["temple-board-row"]):
                                for x in range(game.width):
                                    pos = (x, y)
                                    symbol, color, label = tile_info(game, pos, game.route, player)
                                    solara.Button(symbol, disabled=True,
                                                  classes=["temple-tile"],
                                                  style={"background-color": color, "color": "#fff8ff"},
                                                  title=label)
                    solara.Markdown("? Explorer  ?  ? Key  ?  ? Relic  ?  ? Exit  ?  ? Gate  ?  ? Hazard  ?  ? Trap  ?  ? Mud")

            with solara.Column(gap="12px", style={"flex": "1 1 360px", "min-width": "300px"}):
                with solara.Div(classes=["temple-card"]):
                    solara.Markdown(f"### Explorer {player.player_number} · {mode}")
                    quest = ("Expedition complete!" if player.finished else
                             "Return to the entrance with the relic" if player.has_relic else
                             "Cross the gate and recover the relic" if player.has_key else
                             "Find the ancient key")
                    solara.HTML(tag="div", unsafe_innerHTML=quest, classes=["objective"])
                    with solara.Row(gap="8px", style={"flex-wrap": "wrap"}):
                        for value, label in [(player.moves, "Moves"), (player.cost, "Travel cost"),
                                             (player.trap_hits, "Trap hits")]:
                            with solara.Div(classes=["temple-stat"], style={"flex": "1 1 90px"}):
                                solara.Markdown(f"<strong>{value}</strong><span>{label}</span>")
                    clock_label = "Time remaining" if game.timer_limit else "Time elapsed"
                    seconds = game.remaining() if game.timer_limit else game.elapsed()
                    seconds = seconds or 0
                    solara.Markdown(f"**{clock_label}:** {seconds // 60:02d}:{seconds % 60:02d}")
                    solara.Markdown(f"**Inventory:** {'✓ Key' if player.has_key else '○ Key'}  ·  {'✓ Relic' if player.has_relic else '○ Relic'}")

                with solara.Div(classes=["temple-card"]):
                    if mode == "Human":
                        solara.Markdown("### Move")
                        with solara.Column(gap="5px", style={"align-items": "center"}):
                            solara.Button("↑  North", on_click=lambda: human_move(0, 1), disabled=not can_move, color="#64765b", classes=["move-button"])
                            with solara.Row(gap="5px"):
                                solara.Button("←  West", on_click=lambda: human_move(-1, 0), disabled=not can_move, color="#64765b", classes=["move-button"])
                                solara.Button("↓  South", on_click=lambda: human_move(0, -1), disabled=not can_move, color="#64765b", classes=["move-button"])
                                solara.Button("→  East", on_click=lambda: human_move(1, 0), disabled=not can_move, color="#64765b", classes=["move-button"])
                    else:
                        solara.Markdown("### AI route planner")
                        solara.Markdown("A* finds a low-cost route and adapts as hazards move.")
                        solara.Button("Find route", on_click=plan, disabled=not can_move, color="#bd9651")
                        solara.Select("Step speed", values=["Slow", "Normal", "Fast"], value=speed, on_value=set_speed)
                        with solara.Row(gap="8px"):
                            solara.Button("Pause AI" if running else "Run route", on_click=lambda: set_running(not running), disabled=not game.route or not can_move, color="#64765b")
                            solara.Button("Next step", on_click=next_ai_step, disabled=not game.route or running or not can_move, outlined=True)
                        solara.Markdown(f"**Route length:** {len(game.route)} steps")

                    if len(game.players) > 1:
                        solara.Button(f"Pass turn to Explorer {(player.player_number % len(game.players)) + 1}",
                                      on_click=lambda: (stop_ai(), game.next_player(), redraw()), disabled=game.timed_out)
                    solara.Button("Pause game" if game.paused_at is None else "Resume game",
                                  on_click=lambda: (stop_ai(), game.pause(), redraw()), color="#39483a")

                if len(game.players) > 1:
                    with solara.Div(classes=["temple-card"]):
                        solara.Markdown("### Expedition roster")
                        for explorer in game.players:
                            status = "Escaped" if explorer.finished else "Exploring"
                            solara.Markdown(f"**Explorer {explorer.player_number}:** {status} · {explorer.moves} moves · {explorer.trap_hits} trap hits")

