async function loadBuildingDetails(buildingId) {

    const response =
        await fetch(`/api/building/${buildingId}`);

    const data =
        await response.json();

    const building = data.building;

    document.getElementById("building-details-panel").innerHTML = `
        <section class="unit-details">

            <div class="wiki-header">
                <h2>${building.building_name}</h2>
                <p>${building.building_type}</p>
            </div>

            <div class="wiki-section">
                <h3>Overview</h3>
                <p>${building.overview}</p>
            </div>

            <div class="wiki-section">
                <h3>Economics</h3>

                <div class="stat-grid">

                    <div>Cost: $${building.money_cost.toLocaleString()}</div>

                    <div>CM Cost: ${building.cm_cost}</div>

                    <div>RM Cost: ${building.rm_cost}</div>

                    <div>Build Time: ${building.build_time} Turns</div>

                    <div>Money Upkeep: $${building.money_upkeep.toLocaleString()}</div>

                </div>

            </div>

            <div class="wiki-section">

                <h3>Special Capabilities</h3>

                <p>${building.special_capability}</p>

            </div>

            <div class="wiki-section">

                <h3>Recommended Use</h3>

                <p>${building.recommended_use}</p>

            </div>

        </section>
    `;

}

async function buildBuilding(buildingId) {

    const response =
        await fetch("/api/build-building", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                building_id: buildingId

            })

        });

    const result =
        await response.json();

    if (result.success) {

        NotificationManager.show({

            title: "Construction Started",

            message: `${result.building_name} added to ${result.line}.`,

            icon: "🏗️",

            type: "success"

        });

        await loadConstructionLines();

    }
    else {

        NotificationManager.show({

            title: "Construction Failed",

            message: result.error,

            icon: "❌",

            type: "error"

        });

}}

async function loadConstructionLines() {

    const response =
        await fetch("/api/construction");

    const rows =
        await response.json();

    const groupedLines = {};

    rows.forEach(row => {

        if (!groupedLines[row.line_id]) {

            groupedLines[row.line_id] = {
                line_name: row.line_name,
                queue: []
            };

        }

        if (row.building_name) {

            groupedLines[row.line_id]
                .queue
                .push(row);

        }

    });

    let html = `
        <h2>Construction Firms</h2>
    `;

    Object.values(groupedLines).forEach(line => {

        html += `
            <div class="production-line">

                <h4>${line.line_name}</h4>
        `;

        if (line.queue.length > 0) {

            const active = line.queue[0];

            const progress =
                (
                    (active.build_time - active.turns_remaining)
                    / active.build_time
                ) * 100;

            html += `

                <p>${active.building_name}</p>

                <div class="production-progress">

                    <div
                        class="production-progress-fill"
                        style="width:${progress}%">
                    </div>

                </div>

                <div class="production-status">

                    <span>
                        ${active.turns_remaining}
                        Turns Remaining
                    </span>

                    <button
                        class="cancel-button"
                        onclick="cancelConstruction(${active.queue_id})">

                        Cancel

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
                    .forEach(building => {

                        html += `

                            <div class="queue-item">

                                <span>
                                    • ${building.building_name}
                                </span>

                                <button
                                    class="cancel-button"
                                    onclick="cancelConstruction(${building.queue_id})">

                                    Cancel

                                </button>

                            </div>

                        `;

                    });

            }

        } else {

            html += `

                <p>
                    Ready For Construction
                </p>

            `;

        }

        html += `

            </div>

        `;

    });

    document
        .getElementById("production-panel")
        .innerHTML = html;

}

async function cancelConstruction(queueId) {

    const response =
        await fetch(
            `/api/cancel-construction/${queueId}`,
            {
                method: "DELETE"
            }
        );

    const result =
        await response.json();

    if (result.success) {

        NotificationManager.show({

            title: "Construction Cancelled",

            message: result.message,

            icon: "🚫",

            type: "warning"

        });

    }

    await loadConstructionLines();

}

let currentFilter = "all";

function updateBuildingDisplay() {

    const searchText =
        document.getElementById("building-search")
        .value
        .toLowerCase();

    const cards =
        document.querySelectorAll(".building-card");

    cards.forEach(card => {

        const buildingName =
            card.querySelector("h3")
                .textContent
                .toLowerCase();

        const buildingType =
            card.dataset.class;

        const matchesFilter =
            currentFilter === "all" ||
            buildingType === currentFilter;

        const matchesSearch =
            buildingName.includes(searchText) ||
            buildingType.includes(searchText);

        card.style.display =
            (matchesFilter && matchesSearch)
            ? "flex"
            : "none";

    });

}


document.addEventListener("DOMContentLoaded", () => {

    loadConstructionLines();

    document
        .getElementById("building-search")
        .addEventListener(
            "input",
            updateBuildingDisplay
        );

    document
        .querySelectorAll(".filter-btn")
        .forEach(button => {

            button.addEventListener("click", () => {

                document
                    .querySelectorAll(".filter-btn")
                    .forEach(btn =>
                        btn.classList.remove("active")
                    );

                button.classList.add("active");

                currentFilter =
                    button.dataset.filter;

                updateBuildingDisplay();

            });

        });

    updateBuildingDisplay();

});
