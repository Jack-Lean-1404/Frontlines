/* ==================================================
   MAP CONSTANTS
================================================== */

const MAP_WIDTH = 4260.94;
const MAP_HEIGHT = 2722.26;


/* ==================================================
   MAP STATE
================================================== */

let scale = 1;

let panX = 0;
let panY = 0;

let isPanning = false;

let panStartX = 0;
let panStartY = 0;

let startPanX = 0;
let startPanY = 0;


/* ==================================================
   TEST UNITS
================================================== */

let units = [];

const testUnits = [
    {
        id: 1,
        type: "land",
        nationCode: "SATO",
        tierLevel: 5,
        formationNumber: 1,
        customName: "Spearhead",
        unitIcon:
            "/static/images/unit_icons/Land/mech_f.svg",
        x: 1500,
        y: 1000
    },
    {
        id: 2,
        type: "air",
        nationCode: "SATO",
        tierLevel: 3,
        formationNumber: 2,
        customName: "Alpha",
        unitIcon:
            "/static/images/unit_icons/Air/mrf_e.svg",
        x: 1800,
        y: 1200
    },
    {
        id: 3,
        type: "sea",
        nationCode: "SATO",
        tierLevel: 1,
        formationNumber: 3,
        customName: "War Dogs",
        unitIcon:
            "/static/images/unit_icons/Sea/lcs_n.svg",
        x: 2100,
        y: 900
    }
];

async function loadUnits() {
    try {
        const response = await fetch("/api/tabletop");

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        units = await response.json();

        console.log("Tabletop units loaded:", units);

        renderUnits();

    } catch (error) {
        console.error("Failed to load tabletop units:", error);
    }
}


/* ==================================================
   ELEMENTS
================================================== */

const viewport =
    document.getElementById("map-viewport");

const world =
    document.getElementById("map-world");

const unitsLayer =
    document.getElementById("units-layer");

const coordX =
    document.getElementById("coord-x");

const coordY =
    document.getElementById("coord-y");

const zoomDisplay =
    document.getElementById("zoom");

const deploymentUnits =
    document.getElementById("deployment-units");


/* ==================================================
   UNIT STATE
================================================== */

let selectedUnit = null;

let draggingUnit = false;

let unitStartMouseX = 0;
let unitStartMouseY = 0;

let unitStartX = 0;
let unitStartY = 0;


/* ==================================================
   CREATE UNIT COUNTER
================================================== */

function createUnitCounter(
    unitData,
    addToMap = true
) {
    const counter = document.createElement("div");

    counter.className =
        `unit-counter ${unitData.unit_class}`;

    counter.dataset.unitId =
        unitData.nation_unit_id;

    if (!unitData.isOwn) {
        counter.classList.add("not-owned");
    }

    // Formation size
    const tier = document.createElement("div");
    tier.className = "counter-tier";
    tier.textContent = "X".repeat(unitData.tier_level);

    // Unit image
    const imageContainer = document.createElement("div");
    imageContainer.className = "counter-image";

    const image = document.createElement("img");
    image.src = getUnitIcon(unitData);
    image.draggable = false;

    // Nation code
    const nation = document.createElement("div");
    nation.className = "counter-nation";
    nation.textContent = unitData.nationCode;

    // Formation number
    const formationNumber = document.createElement("div");
    formationNumber.className = "counter-number";
    formationNumber.textContent =
        getOrdinal(unitData.formationNumber);

    // Custom formation name
    const customName = document.createElement("div");
    customName.className = "counter-custom-name";

    if (unitData.customName) {
        customName.textContent = unitData.customName;
    }

    imageContainer.appendChild(image);

    counter.appendChild(tier);
    counter.appendChild(imageContainer);
    counter.appendChild(nation);
    counter.appendChild(formationNumber);
    counter.appendChild(customName);

    // Position only if already placed
    if (
        unitData.x !== null &&
        unitData.y !== null
    ) {
        counter.style.left = `${unitData.x}px`;
        counter.style.top = `${unitData.y}px`;
    }

    counter.addEventListener("mousedown", function(event) {

        event.stopPropagation();

        // Only allow the player's own units
        // to be selected or dragged.
        if (!unitData.isOwn) {
            return;
        }

        selectedUnit = unitData;
        draggingUnit = true;

        counter.classList.add("dragging");

        unitStartMouseX = event.clientX;
        unitStartMouseY = event.clientY;


        /* ------------------------------------------
        UNPLACED UNIT
        ------------------------------------------ */

        if (
            unitData.x === null ||
            unitData.y === null
        ) {

            // Move counter from deployment tray
            // into the map layer
            unitsLayer.appendChild(counter);

            counter.style.position = "absolute";
            counter.style.transform =
                "translate(-50%, -50%)";


            // Get viewport position
            const rect =
                viewport.getBoundingClientRect();


            // Convert mouse position to map coordinates
            const mapX =
                (event.clientX - rect.left - panX) / scale;

            const mapY =
                (event.clientY - rect.top - panY) / scale;


            // Set starting map position
            unitStartX = mapX;
            unitStartY = mapY;


            // Set unit position
            unitData.x = mapX;
            unitData.y = mapY;


            // Position counter
            counter.style.left =
                `${mapX}px`;

            counter.style.top =
                `${mapY}px`;


            updateCoordinates(unitData);

        }


        /* ------------------------------------------
        ALREADY PLACED UNIT
        ------------------------------------------ */

        else {

            unitStartX = unitData.x;
            unitStartY = unitData.y;

            updateCoordinates(unitData);
        }

    });

    if (addToMap) {
        unitsLayer.appendChild(counter);
    }

    return counter;
}

function getOrdinal(number) {
    const lastTwo = number % 100;

    if (lastTwo >= 11 && lastTwo <= 13) {
        return `${number}th`;
    }

    switch (number % 10) {
        case 1:
            return `${number}st`;

        case 2:
            return `${number}nd`;

        case 3:
            return `${number}rd`;

        default:
            return `${number}th`;
    }
}


/* ==================================================
   RENDER ALL UNITS
================================================== */

function renderUnits() {

    unitsLayer.innerHTML = "";
    deploymentUnits.innerHTML = "";

    for (const unitData of units) {

        if (
            unitData.x === null ||
            unitData.y === null
        ) {
            createDeploymentUnit(unitData);
        } else {
            createUnitCounter(unitData);
        }
    }
}

function createDeploymentUnit(unitData) {

    const counter = createUnitCounter(
        unitData,
        false
    );

    counter.classList.add("deployment-unit");

    counter.style.position = "relative";
    counter.style.left = "";
    counter.style.top = "";
    counter.style.transform = "none";

    deploymentUnits.appendChild(counter);

    return counter;
}

/* ==================================================
   UPDATE UNIT POSITION
================================================== */

function updateUnitPosition(
    unitData,
    counter
) {

    counter.style.left =
        `${unitData.x}px`;

    counter.style.top =
        `${unitData.y}px`;
}


/* ==================================================
   UPDATE COORDINATES
================================================== */

function updateCoordinates(unitData) {

    coordX.textContent =
        unitData.x.toFixed(1);

    coordY.textContent =
        unitData.y.toFixed(1);
}


/* ==================================================
   MAP RENDER
================================================== */

function render() {

    world.style.transform =
        `translate(${panX}px, ${panY}px) scale(${scale})`;


    zoomDisplay.textContent =
        `${Math.round(scale * 100)}%`;


    if (selectedUnit) {

        updateCoordinates(
            selectedUnit
        );

    }
}


/* ==================================================
   MAP PAN
================================================== */

viewport.addEventListener(
    "mousedown",
    function(event) {

        if (
            event.target.closest(".unit-counter")
        ) {
            return;
        }


        isPanning = true;


        viewport.classList.add(
            "dragging"
        );


        panStartX =
            event.clientX;

        panStartY =
            event.clientY;


        startPanX =
            panX;

        startPanY =
            panY;
    }
);


window.addEventListener(
    "mousemove",
    function(event) {

        if (!isPanning) {
            return;
        }


        panX =
            startPanX +
            (event.clientX - panStartX);


        panY =
            startPanY +
            (event.clientY - panStartY);


        render();
    }
);


window.addEventListener(
    "mouseup",
    function() {

        isPanning = false;


        viewport.classList.remove(
            "dragging"
        );
    }
);


/* ==================================================
   UNIT DRAG
================================================== */

window.addEventListener(
    "mousemove",
    function(event) {

        if (
            !draggingUnit ||
            !selectedUnit
        ) {
            return;
        }


        const deltaX =
            (
                event.clientX -
                unitStartMouseX
            ) / scale;


        const deltaY =
            (
                event.clientY -
                unitStartMouseY
            ) / scale;


        selectedUnit.x =
            unitStartX + deltaX;


        selectedUnit.y =
            unitStartY + deltaY;


        /* ------------------------------------------
           Keep unit inside map
        ------------------------------------------ */

        selectedUnit.x =
            Math.max(
                0,
                Math.min(
                    MAP_WIDTH,
                    selectedUnit.x
                )
            );


        selectedUnit.y =
            Math.max(
                0,
                Math.min(
                    MAP_HEIGHT,
                    selectedUnit.y
                )
            );


        const counter =
            document.querySelector(
                `[data-unit-id="${selectedUnit.nation_unit_id}"]`
            );


        if (counter) {

            updateUnitPosition(
                selectedUnit,
                counter
            );

        }


        updateCoordinates(
            selectedUnit
        );
    }
);


window.addEventListener("mouseup", function() {

    if (selectedUnit && draggingUnit) {

        const counter =
            document.querySelector(
                `[data-unit-id="${selectedUnit.nation_unit_id}"]`
            );

        if (counter) {
            counter.classList.remove("dragging");
        }

        saveUnitPosition(selectedUnit);
    }

    draggingUnit = false;
});


/* ==================================================
   ZOOM
================================================== */

viewport.addEventListener(
    "wheel",
    function(event) {

        event.preventDefault();


        const zoomFactor =
            event.deltaY < 0
                ? 1.1
                : 0.9;


        const oldScale =
            scale;


        let newScale =
            scale * zoomFactor;


        newScale =
            Math.max(
                0.25,
                Math.min(
                    10,
                    newScale
                )
            );


        /* ------------------------------------------
           Mouse position inside viewport
        ------------------------------------------ */

        const rect =
            viewport.getBoundingClientRect();


        const mouseX =
            event.clientX -
            rect.left;


        const mouseY =
            event.clientY -
            rect.top;


        /* ------------------------------------------
           Map coordinate under mouse
        ------------------------------------------ */

        const mapX =
            (mouseX - panX) /
            oldScale;


        const mapY =
            (mouseY - panY) /
            oldScale;


        /* ------------------------------------------
           Apply zoom
        ------------------------------------------ */

        scale =
            newScale;


        /* ------------------------------------------
           Keep same map point underneath mouse
        ------------------------------------------ */

        panX =
            mouseX -
            mapX * scale;


        panY =
            mouseY -
            mapY * scale;


        render();
    },
    {
        passive: false
    }
);


function getUnitIcon(unitData) {

    const iconName = unitData.unit_icon
        .replace(".png", "")
        .toLowerCase();


    const iconMap = {
        "national_guard": "ng",
        "motorised": "moto",
        "mechanised": "mech",
        "artillery": "art",
        "engineer": "eng",
        "hq": "hq",
        "logistics": "logi",
        "armoured": "arm",

        "af": "af",
        "asf": "asf",
        "ah": "ah",
        "sbomb": "sbomb",

        "lcs": "lcs",
        "ss": "ss"
    };


    const fileName =
        iconMap[iconName];


    if (!fileName) {

        console.error(
            "No tabletop icon found for:",
            unitData.unit_icon
        );

        return "";
    }


    // ==========================================
    // DETERMINE ASSET FOLDER
    // ==========================================

    let folder;


    if (
        iconName === "ah" ||
        iconName === "artillery"
    ) {

        folder = "Land";

    } else if (
        iconName === "ss"
    ) {

        folder = "Sea";

    } else if (
        unitData.unit_class === "land"
    ) {

        folder = "Land";

    } else if (
        unitData.unit_class === "air"
    ) {

        folder = "Air";

    } else if (
        unitData.unit_class === "sea"
    ) {

        folder = "Sea";

    } else {

        console.error(
            "No folder mapping for:",
            unitData.unit_icon,
            unitData.unit_class
        );

        return "";
    }


    // ==========================================
    // DETERMINE RELATIONSHIP
    // ==========================================

    const relationship =
        unitData.relationship
            ? unitData.relationship.toLowerCase()
            : "neutral";


    let relationshipSuffix;


    switch (relationship) {

        case "friendly":
            relationshipSuffix = "f";
            break;

        case "allied":
            relationshipSuffix = "a";
            break;

        case "neutral":
            relationshipSuffix = "n";
            break;

        case "hostile":
            relationshipSuffix = "e";
            break;

        default:

            console.error(
                "Unknown unit relationship:",
                unitData.relationship
            );

            relationshipSuffix = "n";
            break;
    }


    // ==========================================
    // RETURN TABLETOP ICON
    // ==========================================

    return `/static/images/unit_icons/${folder}/${fileName}_${relationshipSuffix}.svg`;
}

async function saveUnitPosition(unitData) {

    try {

        const response = await fetch(
            `/api/tabletop/move/${unitData.nation_unit_id}`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    x: unitData.x,
                    y: unitData.y
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Failed to save position"
            );
        }

        console.log(
            "Unit position saved:",
            result
        );

    } catch (error) {

        console.error(
            "Failed to save unit position:",
            error
        );
    }
}

/* ==================================================
   INITIALISE
================================================== */

loadUnits();
render();