const tierMultipliers = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5
};

function getSelectedTier(unitId) {

    const card =
        document.querySelector(
            `.unit-card[data-unit-id="${unitId}"]`
        );

    return parseInt(
        card.querySelector(".tier-selector").value
    );

}

function getTierMultiplier(unitId) {

    return getSelectedTier(unitId);

}

function getScaledStats(unit, unitId) {

    const multiplier =
        getTierMultiplier(unitId);

    return {

        attack:
            unit.strength * multiplier,

        defence:
            unit.defence * multiplier,

        movement:
            unit.movement,

        size:
            unit.unit_size * multiplier,

        moneyCost:
            unit.money_cost * multiplier,

        cmCost:
            unit.cm_cost * multiplier,

        rmCost:
            unit.rm_cost * multiplier,

        oilUpkeep:
            unit.oil_upkeep * multiplier,

        moneyUpkeep:
            unit.money_upkeep * multiplier,

        buildTime:
            unit.build_time + (multiplier - 1)

    };

}

let currentFilter = "all";

function updateUnitDisplay() {

    console.log("updateUnitDisplay running");

    const searchText =
        document.getElementById("unit-search")
        .value
        .toLowerCase();

    const cards =
        document.querySelectorAll(".unit-card");

    cards.forEach(card => {

        const unitName =
            card.querySelector("h3")
            .textContent
            .toLowerCase();


        const cardClass =
            card.dataset.class;

        const matchesFilter =
            currentFilter === "all" ||
            cardClass === currentFilter;

        const matchesSearch =
            unitName.includes(searchText) ||
            cardClass.includes(searchText);

        if (matchesFilter && matchesSearch) {
            card.style.display = "flex";
        }
        else {
            card.style.display = "none";
        }

    });

}

document.addEventListener("DOMContentLoaded", () => {

    // Filter Buttons
    document.querySelectorAll(".filter-btn").forEach(button => {

        button.addEventListener("click", () => {

            console.log("Clicked:", button.dataset.filter);

            document.querySelectorAll(".filter-btn")
                .forEach(btn => btn.classList.remove("active"));

            button.classList.add("active");

            currentFilter = button.dataset.filter;

            updateUnitDisplay();

        });
    });

    loadProductionLines();

    // Search Bar
    document.getElementById("unit-search")
        .addEventListener("input", () => {

            updateUnitDisplay();

        });

    // Initial page load
    updateUnitDisplay();

    document.querySelectorAll(".tier-selector")
        .forEach(selector => {

            selector.addEventListener("change", () => {

                const card =
                        selector.closest(".unit-card");

                const tierBadge =
                    card.querySelector(".current-tier");

                // console.log(tierBadge);

                if (tierBadge) {
                    tierBadge.textContent =
                        selector.options[selector.selectedIndex].text;
                }

                const tier =
                    parseInt(selector.value);

                const multiplier =
                    tierMultipliers[tier];

                const baseAttack =
                    parseInt(card.dataset.strength);

                const baseDefence =
                    parseInt(card.dataset.defence);

                const baseCost =
                    parseInt(card.dataset.cost);

                const baseBuildTime =
                    parseInt(card.dataset.buildTime);

                card.querySelector(".atk-value")
                    .textContent =
                    baseAttack * multiplier;

                card.querySelector(".def-value")
                    .textContent =
                    baseDefence * multiplier;

                card.querySelector(".cost-value")
                    .textContent =
                    (baseCost * multiplier)
                    .toLocaleString();

                card.querySelector(".build-time-value")
                    .textContent =
                    baseBuildTime * multiplier;

            });

        });

});

async function loadUnitDetails(unitId) {

    

    const response = await fetch(`/api/unit/${unitId}`);

    const data = await response.json();

    const unit = data.unit;
    const resource_units = data.resource_units;

    const stats = getScaledStats(unit, unitId);

    const card =
    document.querySelector(
        `.unit-card[data-unit-id="${unitId}"]`
    );

    const tierSelector =
        card.querySelector(".tier-selector");

    const organisationName =
        tierSelector.options[
            tierSelector.selectedIndex
        ].text;

    // console.log(unit);
    // console.log(unit.organisation_name);

    const strengthsHtml =
    unit.strengths
        .split("\n")
        .map(item => `<li>${item}</li>`)
        .join("");

    const weaknessesHtml =
        unit.weaknesses
            .split("\n")
            .map(item => `<li>${item}</li>`)
            .join("");

    document.getElementById("unit-details-panel")
        .innerHTML = `

        <!-- Unit Wiki -->
        <section class="unit-details">

            <div class="wiki-header">
                <h2>${unit.unit_name}</h2>
                <p>${unit.unit_class} • ${organisationName}</p>
            </div>

            <div class="wiki-section">
                <h3>Overview</h3>
                <p>
                    ${unit.overview}
                </p>
            </div>

            <div class="wiki-section">
                <h3>Combat Statistics</h3>

                <div class="stat-grid">
                    <div>Attack: ${stats.attack}</div>
                    <div>Defence: ${stats.defence}</div>
                    <div>Movement: ${stats.movement}</div>
                    <div>Size: ${stats.size}</div>
                </div>
            </div>

            <div class="wiki-section">
                <h3>Economics</h3>

                <div class="stat-grid">

                    <div>
                        Cost:
                        $${stats.moneyCost.toLocaleString()}
                    </div>

                    <div>
                        CM Cost:
                        ${stats.cmCost}
                        ${resource_units["Common Metal"]}
                    </div>

                    <div>
                        RM Cost:
                        ${stats.rmCost}
                        ${resource_units["Rare Metal"]}
                    </div>

                    <div>
                        Build Time:
                        ${stats.buildTime}
                        Turns
                    </div>

                    <div>
                        Oil Upkeep:
                        ${stats.oilUpkeep}
                        ${resource_units["Oil"]}
                    </div>

                    <div>
                        Money Upkeep:
                        $${stats.moneyUpkeep.toLocaleString()}
                    </div>

                </div>
            </div>

            <div class="wiki-section">

                <h3>Strengths</h3>

                <ul>
                    ${strengthsHtml}
                </ul>

            </div>

            <div class="wiki-section">

                <h3>Weaknesses</h3>

                <ul>
                    ${weaknessesHtml}
                </ul>

            </div>

            <div class="wiki-section">
                <h3>Special Capabilities</h3>
                <p>
                    ${unit.special_capability}
                </p>
            </div>

            <div class="wiki-section">
                <h3>Recommended Employment</h3>
                <p>
                    ${unit.recommended_employment}
                </p>
            </div>

            <button
                onclick="buildUnit(${unit.unit_id})">
                Build
            </button>

        </section>


        `;
    


}

async function buildUnit(unitId) {

    const card =
        document.querySelector(
            `.unit-card[data-unit-id="${unitId}"]`
        );

    const tier =
        parseInt(
            card.querySelector(".tier-selector").value
        );

    const response =
        await fetch("/api/build-unit", {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                unit_id: unitId,
                tier: tier

            })

        });

    const result =
        await response.json();

    if (result.success) {

        NotificationManager.show(result);

        await loadProductionLines();

    }
    else {

        NotificationManager.show({

            title: "Production Failed",

            message: result.error,

            type: "error",

            icon: "❌"

        });

    }
}

async function loadProductionLines() {

    const response =
        await fetch("/api/production");

    const rows =
        await response.json();

    const groupedLines = {};

    rows.forEach(row => {

        if (!groupedLines[row.line_id]) {

            groupedLines[row.line_id] = {
                line_name: row.line_name,
                line_type: row.line_type,
                queue: []
            };

        }

        if (row.unit_name) {

            groupedLines[row.line_id]
                .queue
                .push(row);

        }

    });

    const productionGroups = {
        land: [],
        air: [],
        sea: []
    };

    Object.values(groupedLines)
        .forEach(line => {

            productionGroups[line.line_type]
                .push(line);

        });

    let html = `
        <h2>Production Lines</h2>
    `;

    const categories = [
        {
            key: "land",
            title: "Ground Production"
        },
        {
            key: "air",
            title: "Air Production"
        },
        {
            key: "sea",
            title: "Naval Production"
        }
    ];

    categories.forEach(category => {

        const lines =
            productionGroups[category.key];

        const activeLines =
            lines.filter(
                line => line.queue.length > 0
            ).length;

        html += `
            <div class="production-group">

                <h3>
                    ${category.title}
                    (${activeLines}/${lines.length})
                </h3>
        `;

        lines.forEach(line => {

            html += `
                <div class="production-line">

                    <h4>${line.line_name}</h4>
            `;

            if (line.queue.length > 0) {

                const active =
                    line.queue[0];

                const totalTime =
                    active.build_time +
                    (active.tier - 1);

                const progress =
                    (
                        (totalTime - active.turns_remaining)
                        / totalTime
                    ) * 100;

                html += `
                    <p>
                        ${active.unit_name}
                        ${active.tier_name}
                    </p>

                    <div class="production-progress">

                        <div
                            class="production-progress-fill"
                            style="width: ${progress}%">
                        </div>

                    </div>

                    <div class="production-status">

                        <span>
                            ${active.turns_remaining}
                            Turns Remaining
                        </span>
                        <button
                            class="cancel-button"
                            onclick="cancelQueue(${active.queue_id})">
                            Cancel
                        </button>


                        </button>
                    </div>
                `;

                if (line.queue.length > 1) {

                    html += `
                        <hr>

                        <h5>Queue</h5>
                    `;

                    line.queue
                        .slice(1)
                        .forEach(unit => {

                            html += `
                                <div class="queue-item">

                                    <span>
                                        • ${unit.unit_name}
                                        ${unit.tier_name}
                                    </span>

                                    <button
                                        class="cancel-button"
                                        onclick="cancelQueue(${unit.queue_id})">
                                        Cancel
                                    </button>

                                </div>
                            `;

                        });

                }

            } else {

                html += `
                    <p>
                        Ready For Production
                    </p>
                `;
            }

            html += `
                </div>
            `;

        });

        html += `
            </div>
        `;

    });

    document
        .getElementById("production-panel")
        .innerHTML = html;

}

async function cancelQueue(queueId) {

    const response =
        await fetch(
            `/api/cancel-queue/${queueId}`,
            {
                method: "DELETE"
            }
        );

    const result = await response.json();

    if (result.success) {

        NotificationManager.show(result);

        await loadProductionLines();

    }
    else {

        NotificationManager.show({

            title: "Production Failed",

            message: result.error,

            type: "error",

            icon: "❌"

        });

    }

}