from flask import Flask, render_template, jsonify, request
from rules_engine.game import Game
from rules_engine.player import PlayerState

app = Flask(__name__)
game = Game(["Alice", "Bob", "Charlie"])
game_log = []
game.start_new_round()
game.deal_initial_cards()

@app.route("/")
def index():
    state = build_state()
    return render_template("index.html", state=state)

@app.route("/action", methods=["POST"])
def action():
    data = request.get_json()
    action_type = data.get("action")
    current_player = game.players[game.current_player_index]

    if action_type == "hit":
        game.player_hit(current_player)
    elif action_type == "stay":
        game.player_stay(current_player)

    if game.is_round_over():
        game.end_round()
        if not game.is_game_over():
            game.start_new_round()
    else:
        game.next_active_player()

    return jsonify(build_state())

def build_state():
    return {
        "round": game.round_number,
        "is_game_over": game.is_game_over(),
        "winner": game.get_winner().name if game.is_game_over() else None,
        "current_player": game.players[game.current_player_index].name,
        "log": game.log[-30:],
        "players": [
            {
                "name": p.name,
                "state": p.state.name,
                "number_cards": [c.value for c in p.number_cards],
                "modifier_cards": [c.value.name for c in p.modifier_cards],
                "second_chance_card": p.second_chance_card is not None,
                "total_score": p.total_score,
                "round_score": p.get_round_score(),
            }
            for p in game.players
        ]
    }

if __name__ == "__main__":
    app.run(debug=True)