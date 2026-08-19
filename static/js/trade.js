document.addEventListener("DOMContentLoaded", () => {


    document
        .querySelectorAll(".trade-toggle-button")
        .forEach(button => {

            button.addEventListener("click", () => {

                const targetId =
                    button.dataset.target;

                const section =
                    button.closest(".trade-section");

                /*
                * Remove active state from
                * all buttons in this section.
                */

                section
                    .querySelectorAll(".trade-toggle-button")
                    .forEach(otherButton => {

                        otherButton.classList.remove("active");

                    });


                /*
                * Activate the clicked button.
                */

                button.classList.add("active");


                /*
                * Hide all options and disable
                * their form controls.
                */

                section
                    .querySelectorAll(".trade-option")
                    .forEach(option => {

                        option.style.display = "none";

                        option
                            .querySelectorAll("select, input")
                            .forEach(input => {

                                input.disabled = true;
                                input.required = false;

                            });

                    });


                /*
                * Show the selected option and
                * make its fields required.
                */

                const target =
                    document.getElementById(targetId);

                target.style.display = "block";

                target
                    .querySelectorAll("select, input")
                    .forEach(input => {

                        input.disabled = false;
                        input.required = true;

                    });

            });

        });


    /*
    * Set the initial state.
    *
    * Resources is selected by default,
    * so enable its fields and disable
    * the hidden Unit fields.
    */

    document
        .querySelectorAll(".trade-section")
        .forEach(section => {

            const activeButton =
                section.querySelector(
                    ".trade-toggle-button.active"
                );

            if (!activeButton) {
                return;
            }

            const targetId =
                activeButton.dataset.target;

            section
                .querySelectorAll(".trade-option")
                .forEach(option => {

                    const isActive =
                        option.id === targetId;

                    option.style.display =
                        isActive ? "block" : "none";

                    option
                        .querySelectorAll("select, input")
                        .forEach(input => {

                            input.disabled =
                                !isActive;

                            input.required =
                                isActive;

                        });

                });

        });



        
    const tradeNationSelect =
        document.getElementById(
            "trade-nation-select"
        );


    const receiverUnitSelect =
        document.getElementById(
            "receiver-unit-select"
        );


    tradeNationSelect.addEventListener(
        "change",
        async function () {

            const nationId =
                this.value;


            receiverUnitSelect.innerHTML = `

                <option value="">
                    Select Unit
                </option>

            `;


            if (!nationId) {

                return;

            }


            try {

                const response =
                    await fetch(
                        `/api/trade/nation/${nationId}/units`
                    );


                const result =
                    await response.json();


                if (
                    !response.ok ||
                    !result.success
                ) {

                    NotificationManager.show({

                        title: "Trade Error",

                        message:
                            result.error ||
                            "Unable to load units.",

                        type: "error",

                        icon: "❌"

                    });

                    return;

                }


                result.units.forEach(
                    unit => {

                        const option =
                            document.createElement(
                                "option"
                            );


                        /*
                        * We need both unit_id
                        * and tier_level because:
                        *
                        * Motorised Infantry Company
                        * and
                        * Motorised Infantry Battalion
                        *
                        * have the same unit_id.
                        */

                        option.value =
                            `${unit.unit_id}:${unit.tier_level}`;


                        option.textContent =
                            `${unit.unit_name} ${
                                unit.tier_name
                            } — ${
                                Number(
                                    unit.quantity
                                ).toLocaleString()
                            }`;


                        receiverUnitSelect
                            .appendChild(option);

                    }
                );

            }

            catch (error) {

                console.error(
                    "Failed to load nation units:",
                    error
                );


                NotificationManager.show({

                    title: "Trade Error",

                    message:
                        "Unable to load the selected nation's units.",

                    type: "error",

                    icon: "❌"

                });

            }

        }

    );



    document
        .querySelectorAll(".trade-accept-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                async function () {

                    const tradeId =
                        this.dataset.tradeId;


                    this.disabled = true;


                    try {

                        const response =
                            await fetch(
                                `/api/trade/${tradeId}/accept`,
                                {
                                    method: "POST"
                                }
                            );


                        const result =
                            await response.json();


                        NotificationManager.show(
                            result
                        );


                        if (result.success) {

                            setTimeout(() => {

                                location.reload();

                            }, 500);

                        }

                        else {

                            this.disabled = false;

                        }

                    }

                    catch (error) {

                        console.error(
                            "Trade acceptance failed:",
                            error
                        );


                        NotificationManager.show({

                            title: "Trade Failed",

                            message:
                                "Unable to process the trade.",

                            type: "error",

                            icon: "❌"

                        });


                        this.disabled = false;

                    }

                }
            );

        });


    document
        .querySelectorAll(".trade-decline-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                async function () {

                    const tradeId =
                        this.dataset.tradeId;


                    this.disabled = true;


                    try {

                        const response =
                            await fetch(
                                `/api/trade/${tradeId}/decline`,
                                {
                                    method: "POST"
                                }
                            );


                        const result =
                            await response.json();


                        NotificationManager.show(
                            result
                        );


                        if (result.success) {

                            setTimeout(() => {

                                location.reload();

                            }, 500);

                        }

                        else {

                            this.disabled = false;

                        }

                    }

                    catch (error) {

                        console.error(
                            "Trade decline failed:",
                            error
                        );


                        NotificationManager.show({

                            title: "Trade Failed",

                            message:
                                "Unable to decline the trade.",

                            type: "error",

                            icon: "❌"

                        });


                        this.disabled = false;

                    }

                }
            );

        });

});
