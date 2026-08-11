const NotificationManager = {

    history: [],

    show(notification) {

        const container =
            document.getElementById("notification-container");

        if (!container) {

            return;

        }


        const card =
            document.createElement("div");

        card.className =
            `notification ${notification.type}`;


        let actions = "";


        /*
         * Actionable notifications
         *
         * Alliance invitations:
         * Accept / Decline
         *
         * Trade offers:
         * Accept / Decline
         */

        if (
            notification.type === "alliance_invitation" ||
            notification.type === "trade_offer"
        ) {

            actions = `

                <div class="notification-actions">

                    <button
                        class="notification-accept">

                        Accept

                    </button>

                    <button
                        class="notification-decline">

                        Decline

                    </button>

                </div>

            `;

        }


        card.innerHTML = `

            <div class="notification-header">

                <span class="notification-icon">
                    ${notification.icon}
                </span>

                <span>
                    ${notification.title}
                </span>

            </div>

            <div class="notification-body">

                ${notification.message}

            </div>

            ${actions}

        `;


        container.appendChild(card);


        /*
         * Handle actionable notifications
         */

        if (
            notification.type === "alliance_invitation" ||
            notification.type === "trade_offer"
        ) {

            const acceptButton =
                card.querySelector(
                    ".notification-accept"
                );

            const declineButton =
                card.querySelector(
                    ".notification-decline"
                );


            let acceptUrl;
            let declineUrl;


            /*
             * Alliance invitation endpoints
             */

            if (
                notification.type ===
                "alliance_invitation"
            ) {

                acceptUrl =
                    `/api/alliance-invitation/${notification.reference_id}/accept`;

                declineUrl =
                    `/api/alliance-invitation/${notification.reference_id}/decline`;

            }


            /*
             * Trade offer endpoints
             */

            else if (
                notification.type ===
                "trade_offer"
            ) {

                acceptUrl =
                    `/api/trade/${notification.reference_id}/accept`;

                declineUrl =
                    `/api/trade/${notification.reference_id}/decline`;

            }


            /*
             * ACCEPT
             */

            acceptButton.addEventListener(
                "click",
                async (event) => {

                    event.stopPropagation();


                    acceptButton.disabled = true;

                    declineButton.disabled = true;


                    try {

                        const response =
                            await fetch(
                                acceptUrl,
                                {
                                    method: "POST"
                                }
                            );


                        const result =
                            await response.json();


                        /*
                         * Remove the actionable
                         * notification.
                         */

                        NotificationManager.remove(
                            card
                        );


                        /*
                         * Display the result
                         */

                        NotificationManager.show(
                            result
                        );


                        /*
                         * Refresh the page after
                         * successful action.
                         */

                        if (result.success) {

                            setTimeout(() => {

                                location.reload();

                            }, 500);

                        }

                        else {

                            acceptButton.disabled =
                                false;

                            declineButton.disabled =
                                false;

                        }

                    }

                    catch (error) {

                        console.error(
                            "Notification action failed:",
                            error
                        );


                        NotificationManager.remove(
                            card
                        );


                        NotificationManager.show({

                            title:
                                "Action Failed",

                            message:
                                "Unable to process the request.",

                            type:
                                "error",

                            icon:
                                "❌",

                            duration:
                                6000

                        });

                    }

                }
            );


            /*
             * DECLINE
             */

            declineButton.addEventListener(
                "click",
                async (event) => {

                    event.stopPropagation();


                    acceptButton.disabled = true;

                    declineButton.disabled = true;


                    try {

                        const response =
                            await fetch(
                                declineUrl,
                                {
                                    method: "POST"
                                }
                            );


                        const result =
                            await response.json();


                        /*
                         * Remove the actionable
                         * notification.
                         */

                        NotificationManager.remove(
                            card
                        );


                        /*
                         * Display result
                         */

                        NotificationManager.show(
                            result
                        );


                        /*
                         * Refresh trade/alliance
                         * state.
                         */

                        if (result.success) {

                            setTimeout(() => {

                                location.reload();

                            }, 500);

                        }

                    }

                    catch (error) {

                        console.error(
                            "Notification action failed:",
                            error
                        );


                        NotificationManager.remove(
                            card
                        );


                        NotificationManager.show({

                            title:
                                "Action Failed",

                            message:
                                "Unable to process the request.",

                            type:
                                "error",

                            icon:
                                "❌",

                            duration:
                                6000

                        });

                    }

                }
            );

        }


        /*
         * Persistent notifications stay visible
         * until the player takes an action.
         */

        if (notification.persistent) {

            return;

        }


        /*
         * Normal notifications disappear
         * automatically.
         */

        const duration =
            notification.duration || 6000;


        let timeout =
            setTimeout(() => {

                NotificationManager.remove(
                    card
                );

            }, duration);


        card.addEventListener(
            "mouseenter",
            () => {

                clearTimeout(timeout);

            }
        );


        card.addEventListener(
            "mouseleave",
            () => {

                timeout =
                    setTimeout(() => {

                        NotificationManager.remove(
                            card
                        );

                    }, 1500);

            }
        );

    },


    /*
     * Remove notification
     */

    remove(card) {

        card.style.opacity = "0";

        card.style.transform =
            "translateX(50px)";


        setTimeout(() => {

            card.remove();

        }, 300);

    }

};

async function loadNotifications() {

    const response =
        await fetch("/api/notifications");

    if (!response.ok) {

        return;

    }


    const notifications =
        await response.json();


    notifications.forEach(notification => {

        NotificationManager.show(
            notification
        );


        fetch(
            `/api/notifications/${notification.notification_id}/read`,
            {
                method: "POST"
            }
        );

    });

}

async function loadRecentEvents() {

    const response =
        await fetch("/api/events");

    if (!response.ok) {

        return;

    }


    const events =
        await response.json();


    const container =
        document.getElementById("recent-events");


    if (!container) {

        return;

    }


    container.innerHTML = "";


    /*
     * No events
     */

    if (events.length === 0) {

        container.innerHTML = `

            <div class="recent-event-empty">

                <span class="recent-event-icon">
                    ℹ
                </span>

                <div>

                    <strong>
                        No recent events
                    </strong>

                    <p>
                        Events such as completed construction,
                        completed production, research,
                        diplomacy, and combat reports
                        will appear here.
                    </p>

                </div>

            </div>

        `;

        return;

    }


    /*
     * Display events
     */

    events.forEach(event => {

        const eventElement =
            document.createElement("div");


        eventElement.className =
            "recent-event";


        eventElement.innerHTML = `

            <div class="recent-event-icon">
                ℹ
            </div>

            <div class="recent-event-content">

                <strong>
                    ${event.title}
                </strong>

                <p>
                    ${event.message}
                </p>

                <small>
                    Turn ${event.created_turn}
                </small>

            </div>

        `;


        container.appendChild(
            eventElement
        );

    });

}

loadRecentEvents();

loadNotifications();


// Check for new notifications every 5 seconds

setInterval(() => {

    loadNotifications();

}, 5000);