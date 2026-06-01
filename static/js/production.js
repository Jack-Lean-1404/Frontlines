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

function loadUnitDetails(unitId) {
    console.log("Loading unit:", unitId);
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

                card.querySelector(".current-tier")
                    .textContent =
                    selector.options[selector.selectedIndex].text;

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
                <p>${unit.unit_class} • ${unit.organisation_name}</p>
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

            <button class="build-btn">
                Build Unit
            </button>

        </section>


        `;
    
}