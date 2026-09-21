// Инициализация Telegram Mini App
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// Таблица эффективности типов (та же, что в Python)
const STRONG_AGAINST = {
    normal:   [],
    fighting: ["normal", "rock", "ice", "dark", "steel"],
    flying:   ["fighting", "bug", "grass"],
    poison:   ["grass", "fairy"],
    ground:   ["poison", "rock", "fire", "electric", "steel"],
    rock:     ["flying", "bug", "fire", "ice"],
    bug:      ["grass", "psychic", "dark"],
    ghost:    ["ghost", "psychic"],
    steel:    ["ice", "rock", "fairy"],
    fire:     ["bug", "grass", "ice", "steel"],
    water:    ["ground", "rock", "fire"],
    grass:    ["ground", "rock", "water"],
    electric: ["flying", "water"],
    psychic:  ["fighting", "poison"],
    ice:      ["flying", "ground", "grass", "dragon"],
    dragon:   ["dragon"],
    dark:     ["ghost", "psychic"],
    fairy:    ["fighting", "dragon", "dark"],
};

const POKEAPI = "https://pokeapi.co/api/v2/pokemon";

// Состояние
let team = [];
let opponents = [];

// DOM
const teamChips = document.getElementById("team-chips");
const opponentChips = document.getElementById("opponent-chips");
const teamInput = document.getElementById("team-input");
const opponentInput = document.getElementById("opponent-input");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const analyzeBtn = document.getElementById("analyze");

// ─── Chips ────────────────────────────────────────────────

function renderChips() {
    teamChips.innerHTML = team.map((name, i) =>
        `<span class="chip">${name}<span class="chip-remove" data-type="team" data-index="${i}">×</span></span>`
    ).join("");

    opponentChips.innerHTML = opponents.map((name, i) =>
        `<span class="chip">${name}<span class="chip-remove" data-type="opponent" data-index="${i}">×</span></span>`
    ).join("");
}

document.addEventListener("click", (e) => {
    if (e.target.classList.contains("chip-remove")) {
        const type = e.target.dataset.type;
        const index = parseInt(e.target.dataset.index);
        if (type === "team") team.splice(index, 1);
        else opponents.splice(index, 1);
        renderChips();
    }
});

function addToTeam() {
    const value = teamInput.value.trim().toLowerCase();
    if (!value) return;
    if (team.length >= 6) {
        showStatus("В команде не может быть больше 6 покемонов");
        return;
    }
    team.push(value);
    teamInput.value = "";
    renderChips();
}

function addToOpponent() {
    const value = opponentInput.value.trim().toLowerCase();
    if (!value) return;
    opponents.push(value);
    opponentInput.value = "";
    renderChips();
}

document.getElementById("team-add").addEventListener("click", addToTeam);
document.getElementById("opponent-add").addEventListener("click", addToOpponent);

teamInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") addToTeam();
});
opponentInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") addToOpponent();
});

// ─── PokéAPI ──────────────────────────────────────────────

async function fetchPokemon(name) {
    try {
        const response = await fetch(`${POKEAPI}/${name}`);
        if (response.status === 404) {
            return { error: `Покемон "${name}" не найден` };
        }
        if (!response.ok) {
            return { error: `PokéAPI вернул ошибку ${response.status}` };
        }
        const data = await response.json();
        return {
            name: data.name,
            types: data.types.map(t => t.type.name),
            stats: Object.fromEntries(
                data.stats.map(s => [s.stat.name, s.base_stat])
            ),
            abilities: data.abilities.map(a => a.ability.name),
        };
    } catch (err) {
        return { error: "Не удалось связаться с PokéAPI. Проверь интернет." };
    }
}

// ─── Анализ ───────────────────────────────────────────────

function weaknessesOf(types) {
    const result = {};
    for (const [attackType, defendedTypes] of Object.entries(STRONG_AGAINST)) {
        const hits = types.filter(t => defendedTypes.includes(t)).length;
        if (hits > 0) {
            result[attackType] = Math.pow(2, hits);
        }
    }
    return result;
}

function teamWeaknessSummary(teamData) {
    const summary = {};
    for (const pokemon of teamData) {
        for (const attackType of Object.keys(weaknessesOf(pokemon.types))) {
            summary[attackType] = (summary[attackType] || 0) + 1;
        }
    }
    return summary;
}

/**
 * Идея 2: найти покемонов команды, которых противник бьёт больно.
 *
 * Смотрим типы противника. Для каждого покемона команды проверяем,
 * есть ли среди них тот, что бьёт его сильно. Возвращаем список
 * уязвимых, отсортированный по множителю (самые уязвимые — сверху).
 */
function vulnerableAgainstOpponent(teamData, opponentData) {
    const opponentTypes = opponentData.types;
    const vulnerable = [];

    for (const p of teamData) {
        const weaknesses = weaknessesOf(p.types);
        const hits = opponentTypes.filter(t => weaknesses[t]);
        if (hits.length > 0) {
            const maxMultiplier = Math.max(...hits.map(t => weaknesses[t]));
            vulnerable.push({
                name: p.name,
                multiplier: maxMultiplier,
                types: hits,
            });
        }
    }

    return vulnerable.sort((a, b) => b.multiplier - a.multiplier);
}

// ─── Отображение ──────────────────────────────────────────

function showStatus(text) {
    statusEl.textContent = text;
    statusEl.classList.remove("hidden");
}

function hideStatus() {
    statusEl.classList.add("hidden");
}

function typeBadge(type) {
    return `<span class="type-badge type-${type}">${type}</span>`;
}

function renderPokemonCard(pokemon) {
    const weaknesses = weaknessesOf(pokemon.types);
    const sorted = Object.entries(weaknesses).sort((a, b) => b[1] - a[1]);

    const weaknessHtml = sorted.map(([type, mult]) =>
        `<span class="weakness-item ${mult >= 4 ? "critical" : ""}">${type} ×${mult}</span>`
    ).join("");

    return `
        <div class="pokemon-card">
            <div class="name">${pokemon.name}</div>
            <div class="types">${pokemon.types.map(typeBadge).join("")}</div>
            <div class="weakness-list">${weaknessHtml}</div>
        </div>
    `;
}

function renderResult(teamData, summary, proposal, sources, opponentData, vulnerable) {
    const sortedSummary = Object.entries(summary).sort((a, b) => b[1] - a[1]);

    let html = "";

    // Команда
    html += "<h2>Команда</h2>";
    html += teamData.map(renderPokemonCard).join("");

    // Слабости команды
    html += "<h2>Слабости команды</h2>";
    if (sortedSummary.length === 0) {
        html += "<p>Серьёзных слабостей не найдено.</p>";
    } else {
        html += '<div class="weakness-list">';
        for (const [type, count] of sortedSummary) {
            html += `<span class="weakness-item ${count >= 3 ? "critical" : ""}">${type}: ${count} покемонов</span>`;
        }
        html += "</div>";
    }

    // Против противника
    if (opponentData) {
        html += `<h2>Против ${opponentData.name}</h2>`;
        html += `<div class="types" style="margin-bottom:12px">${opponentData.types.map(typeBadge).join("")}</div>`;

        if (vulnerable.length === 0) {
            html += `<p>Команда устойчива к атакам противника.</p>`;
        } else {
            html += `<p style="color:#ff9800;margin-bottom:8px">⚠️ Осторожно, ${opponentData.name} бьёт больно:</p>`;
            html += '<div class="weakness-list">';
            for (const v of vulnerable) {
                const types = v.types.join(", ");
                html += `<span class="weakness-item ${v.multiplier >= 4 ? "critical" : ""}">${v.name}: ${types} ×${v.multiplier}</span>`;
            }
            html += "</div>";
        }
    }

    // Замена
    if (proposal) {
        html += `
            <div class="proposal">
                <p><strong>Предложенная замена:</strong></p>
                <p>Убрать: <strong>${proposal.out}</strong></p>
                <p>Добавить: покемона, устойчивого к типу <strong>${proposal.mainWeakness}</strong></p>
            </div>
        `;
    }

    // Источники
    html += "<h2>Источники</h2>";
    html += '<div class="sources">';
    for (const src of sources) {
        html += `<a href="${src}" target="_blank">${src}</a><br>`;
    }
    html += "</div>";

    resultEl.innerHTML = html;
    resultEl.classList.remove("hidden");
}

// ─── Основная логика ──────────────────────────────────────

async function analyze() {
    if (team.length === 0 || opponents.length === 0) {
        showStatus("Нужно указать и команду, и противника");
        return;
    }

    analyzeBtn.disabled = true;
    resultEl.classList.add("hidden");
    showStatus("Загружаю данные из PokéAPI…");

    try {
        const allNames = [...team, ...opponents];
        const responses = await Promise.all(allNames.map(fetchPokemon));

        const teamData = [];
        const sources = [];
        let error = null;

        for (let i = 0; i < allNames.length; i++) {
            const data = responses[i];
            if (data.error) {
                error = data.error;
                break;
            }
            if (i < team.length) teamData.push(data);
            sources.push(`${POKEAPI}/${data.name}`);
        }

        if (error) {
            showStatus(`Ошибка: ${error}`);
            return;
        }

        // Противник — первый из opponents (последний в responses после teamData)
        const opponentData = responses[responses.length - 1];

        showStatus("Считаю слабости…");
        const summary = teamWeaknessSummary(teamData);
        const vulnerable = vulnerableAgainstOpponent(teamData, opponentData);

        // Простая эвристика: убрать самого слабого
        let worstName = null;
        let worstCount = -1;
        for (const p of teamData) {
            const count = Object.keys(weaknessesOf(p.types)).length;
            if (count > worstCount) {
                worstCount = count;
                worstName = p.name;
            }
        }

        const mainWeakness = Object.keys(summary).sort(
            (a, b) => summary[b] - summary[a]
        )[0];

        const proposal = worstName ? {
            out: worstName,
            mainWeakness: mainWeakness,
        } : null;

        hideStatus();
        renderResult(teamData, summary, proposal, sources, opponentData, vulnerable);

    } catch (err) {
        showStatus(`Ошибка: ${err.message}`);
    } finally {
        analyzeBtn.disabled = false;
    }
}

analyzeBtn.addEventListener("click", analyze);