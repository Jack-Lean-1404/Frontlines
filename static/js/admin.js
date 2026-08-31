document.addEventListener("DOMContentLoaded", function () {

    const buildingSelect = document.getElementById("buildingSelect");
    const resourceContainer = document.getElementById("resourceContainer");
    const resourceSelect = document.getElementById("resourceSelect");
    const buildingResourceData = document.getElementById("buildingResourceData");

    // Make sure the elements exist
    if (
        !buildingSelect ||
        !resourceContainer ||
        !resourceSelect ||
        !buildingResourceData
    ) {
        return;
    }

    buildingSelect.addEventListener("change", function () {

        const buildingId = this.value;

        // Clear existing resource options
        resourceSelect.innerHTML =
            '<option value="">Select Resource</option>';

        // Find resource options for this building
        const resourceOptions = buildingResourceData.querySelectorAll(
            '[data-building-id="' + buildingId + '"]'
        );

        // No resources associated with this building
        if (resourceOptions.length === 0) {

            resourceContainer.style.display = "none";
            resourceSelect.required = false;

            return;
        }

        // Show resource selector
        resourceContainer.style.display = "block";
        resourceSelect.required = true;

        // Add resources
        resourceOptions.forEach(function (resource) {

            const option = document.createElement("option");

            option.value = resource.dataset.resourceId;
            option.textContent = resource.dataset.resourceName;

            resourceSelect.appendChild(option);

        });

    });

});

// -------------------------
// REMOVE BUILDING
// -------------------------

const removeBuildingSelect =
    document.getElementById("removeBuildingSelect");

const removeResourceContainer =
    document.getElementById("removeResourceContainer");

const removeResourceSelect =
    document.getElementById("removeResourceSelect");


if (
    removeBuildingSelect &&
    removeResourceContainer &&
    removeResourceSelect &&
    buildingResourceData
) {

    removeBuildingSelect.addEventListener("change", function () {

        const buildingId = this.value;

        // Clear existing resource options
        removeResourceSelect.innerHTML =
            '<option value="">Select Resource</option>';

        // Find resources for this building
        const resourceOptions =
            buildingResourceData.querySelectorAll(
                '[data-building-id="' + buildingId + '"]'
            );

        // No resource options
        if (resourceOptions.length === 0) {

            removeResourceContainer.style.display = "none";
            removeResourceSelect.required = false;

            return;
        }

        // Show resource selector
        removeResourceContainer.style.display = "block";
        removeResourceSelect.required = true;

        // Add resources
        resourceOptions.forEach(function (resource) {

            const option = document.createElement("option");

            option.value = resource.dataset.resourceId;
            option.textContent = resource.dataset.resourceName;

            removeResourceSelect.appendChild(option);

        });

    });

}

// -------------------------
// TRANSFER BUILDING
// -------------------------

const transferBuildingSelect =
    document.getElementById("transferBuildingSelect");

const transferResourceContainer =
    document.getElementById("transferResourceContainer");

const transferResourceSelect =
    document.getElementById("transferResourceSelect");


if (
    transferBuildingSelect &&
    transferResourceContainer &&
    transferResourceSelect &&
    buildingResourceData
) {

    transferBuildingSelect.addEventListener("change", function () {

        const buildingId = this.value;

        // Clear existing resource options
        transferResourceSelect.innerHTML =
            '<option value="">Select Resource</option>';

        // Find resources for this building
        const resourceOptions =
            buildingResourceData.querySelectorAll(
                '[data-building-id="' + buildingId + '"]'
            );

        // No resource options
        if (resourceOptions.length === 0) {

            transferResourceContainer.style.display = "none";
            transferResourceSelect.required = false;

            return;
        }

        // Show resource selector
        transferResourceContainer.style.display = "block";
        transferResourceSelect.required = true;

        // Add resources
        resourceOptions.forEach(function (resource) {

            const option = document.createElement("option");

            option.value = resource.dataset.resourceId;
            option.textContent = resource.dataset.resourceName;

            transferResourceSelect.appendChild(option);

        });

    });

}