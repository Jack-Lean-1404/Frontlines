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
   TEST UNIT DATA
================================================== */

const testUnit = {

    nationCode: "SATO",

    tierLevel: 5,

    unitIcon:
        "/static/images/unit_icons/Mechanised_Infantry.png"
};


/* ==================================================
   TEST UNIT POSITION
================================================== */

let unitX = 1500;
let unitY = 1000;


/* ==================================================
   ELEMENTS
================================================== */

const viewport =
    document.getElementById("map-viewport");

const world =
    document.getElementById("map-world");

const unit =
    document.getElementById("test-unit");

const coordX =
    document.getElementById("coord-x");

const coordY =
    document.getElementById("coord-y");

const zoomDisplay =
    document.getElementById("zoom");


/* ==================================================
   COUNTER UPDATE
================================================== */

function updateCounter() {

    const tier =
        "X".repeat(testUnit.tierLevel);

    document.querySelector(
        ".counter-tier"
    ).textContent = tier;


    document.querySelector(
        ".counter-nation"
    ).textContent = testUnit.nationCode;


    document.getElementById(
        "unit-icon"
    ).src = testUnit.unitIcon;
}


/* ==================================================
   MAP RENDER
================================================== */

function render() {

    world.style.transform =
        `translate(${panX}px, ${panY}px) scale(${scale})`;


    unit.style.left =
        `${unitX}px`;

    unit.style.top =
        `${unitY}px`;


    coordX.textContent =
        unitX.toFixed(1);

    coordY.textContent =
        unitY.toFixed(1);


    zoomDisplay.textContent =
        `${Math.round(scale * 100)}%`;
}


/* ==================================================
   MAP PAN
================================================== */

viewport.addEventListener(
    "mousedown",
    function(event) {

        if (event.target === unit) {
            return;
        }


        isPanning = true;

        viewport.classList.add("dragging");


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

        viewport.classList.remove("dragging");
    }
);


/* ==================================================
   UNIT DRAG
================================================== */

let draggingUnit = false;

let unitStartMouseX = 0;
let unitStartMouseY = 0;

let unitStartX = 0;
let unitStartY = 0;


unit.addEventListener(
    "mousedown",
    function(event) {

        event.stopPropagation();


        draggingUnit = true;

        unit.classList.add("dragging");


        unitStartMouseX =
            event.clientX;

        unitStartMouseY =
            event.clientY;


        unitStartX =
            unitX;

        unitStartY =
            unitY;
    }
);


window.addEventListener(
    "mousemove",
    function(event) {

        if (!draggingUnit) {
            return;
        }


        const deltaX =
            (event.clientX - unitStartMouseX)
            / scale;


        const deltaY =
            (event.clientY - unitStartMouseY)
            / scale;


        unitX =
            unitStartX + deltaX;

        unitY =
            unitStartY + deltaY;


        /* ------------------------------------------
           Keep unit inside map
        ------------------------------------------ */

        unitX =
            Math.max(
                0,
                Math.min(
                    MAP_WIDTH,
                    unitX
                )
            );


        unitY =
            Math.max(
                0,
                Math.min(
                    MAP_HEIGHT,
                    unitY
                )
            );


        render();
    }
);


window.addEventListener(
    "mouseup",
    function() {

        draggingUnit = false;

        unit.classList.remove("dragging");
    }
);


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
            event.clientX - rect.left;

        const mouseY =
            event.clientY - rect.top;


        /* ------------------------------------------
           Map coordinate under mouse
        ------------------------------------------ */

        const mapX =
            (mouseX - panX) / oldScale;


        const mapY =
            (mouseY - panY) / oldScale;


        /* ------------------------------------------
           Apply new zoom
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


/* ==================================================
   INITIALISE
================================================== */

updateCounter();

render();