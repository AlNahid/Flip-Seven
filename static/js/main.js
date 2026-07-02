async function sendAction(actionType) {
    const response = await fetch("/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionType })
    });
    const state = await response.json();
    updateUI(state);
}

function updateUI(state) {
    // Round info
    document.getElementById("round-number").textContent = state.round;
    document.getElementById("current-player").textContent = state.current_player;
    document.getElementById("status-message").textContent = `${state.current_player}'s turn`;

    // Players — sort by name to match Jinja sort
    const sorted = [...state.players].sort((a, b) => a.name.localeCompare(b.name));
    sorted.forEach(player => {
        const el = document.getElementById(`player-${player.name}`);
        if (!el) return;

        // Active turn highlight
        el.classList.toggle("active-turn", player.name === state.current_player);

        // State badge
        const stateBadge = el.querySelector(".player-state");
        stateBadge.textContent = player.state;
        stateBadge.className = `player-state ${player.state.toLowerCase()}`;

        // Scores
        const scores = el.querySelectorAll(".player-scores strong");
        scores[0].textContent = player.round_score;
        scores[1].textContent = player.total_score;

        // Cards
        const cardValues = el.querySelectorAll(".card-values");
        cardValues[0].textContent = player.number_cards.join(", ") || "—";
        cardValues[1].textContent = player.modifier_cards.join(", ") || "—";

        // Second chance
        const scEl = cardValues[2];
        if (player.second_chance_card) {
            scEl.textContent = "✓ Held";
            scEl.classList.add("has-sc");
        } else {
            scEl.textContent = "—";
            scEl.classList.remove("has-sc");
        }
    });

    // Log — newest at bottom, auto-scroll
    const logList = document.getElementById("log-list");
    logList.innerHTML = "";
    state.log.forEach(entry => {
        const li = document.createElement("li");
        li.textContent = entry;
        if (entry.includes("---")) li.classList.add("log-divider");
        logList.appendChild(li);
    });
    logList.scrollTop = logList.scrollHeight;

    // Game over
    if (state.is_game_over) {
        document.getElementById("game-over").style.display = "block";
        document.getElementById("winner-name").textContent = state.winner;
        document.getElementById("hit-btn").disabled = true;
        document.getElementById("stay-btn").disabled = true;
        document.getElementById("status-message").textContent = "Game over!";
    }
}