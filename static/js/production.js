const tierMultipliers = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5
};

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