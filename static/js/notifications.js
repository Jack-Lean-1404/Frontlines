const NotificationManager = {

    history: [],

    show(notification) {

        const container =
            document.getElementById("notification-container");

        const card =
            document.createElement("div");

        card.className =
            `notification ${notification.type}`;

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
        `;

        container.appendChild(card);

        card.addEventListener("click", () => {

            NotificationManager.remove(card);

        });

        const duration = notification.duration || 4000;

        let timeout = setTimeout(() => {

            NotificationManager.remove(card);

        }, duration);

        card.addEventListener("mouseenter", () => {

            clearTimeout(timeout);
            
        });

        card.addEventListener("mouseleave", () => {

            timeout = setTimeout(() => {

                NotificationManager.remove(card);

            }, 1500);

        });


    },

    remove(card) {

        card.style.opacity = "0";
        card.style.transform = "translateX(50px)";

        setTimeout(() => {

            card.remove();

        }, 300);

    }

};