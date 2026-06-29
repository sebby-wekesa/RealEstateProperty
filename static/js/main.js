document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("js-ready");

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const finePointer = window.matchMedia("(pointer: fine)");
    const canUseSpotlight = () => finePointer.matches && !reduceMotion.matches && window.innerWidth > 1024;

    if (canUseSpotlight()) {
        const cursorGlow = document.createElement("div");
        cursorGlow.id = "mouse-follower";
        cursorGlow.className = "cursor-glow";
        cursorGlow.setAttribute("aria-hidden", "true");
        document.body.appendChild(cursorGlow);
        document.body.classList.add("js-spotlight");

        let pointerX = window.innerWidth / 2;
        let pointerY = window.innerHeight / 2;
        let frameId = null;

        const renderSpotlight = () => {
            cursorGlow.style.transform = `translate3d(${pointerX}px, ${pointerY}px, 0) translate(-50%, -50%)`;
            document.documentElement.style.setProperty("--spotlight-x", `${pointerX}px`);
            document.documentElement.style.setProperty("--spotlight-y", `${pointerY}px`);
            frameId = null;
        };

        const queueSpotlight = (event) => {
            pointerX = event.clientX;
            pointerY = event.clientY;
            cursorGlow.classList.add("is-visible");

            if (frameId === null) {
                frameId = window.requestAnimationFrame(renderSpotlight);
            }
        };

        window.addEventListener("pointermove", queueSpotlight);
        window.addEventListener("pointerleave", () => cursorGlow.classList.remove("is-visible"));
    }

    if (finePointer.matches && !reduceMotion.matches) {
        const reactiveCards = document.querySelectorAll(".property-card, .card");

        reactiveCards.forEach((card) => {
            card.addEventListener("pointermove", (event) => {
                const rect = card.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                const tiltY = ((x / rect.width) - 0.5) * 7;
                const tiltX = ((0.5 - (y / rect.height)) * 7);

                card.style.setProperty("--card-x", `${x}px`);
                card.style.setProperty("--card-y", `${y}px`);
                card.style.setProperty("--tilt-x", `${tiltX.toFixed(2)}deg`);
                card.style.setProperty("--tilt-y", `${tiltY.toFixed(2)}deg`);
                card.classList.add("is-pointer-active");
            });

            card.addEventListener("pointerleave", () => {
                card.style.setProperty("--tilt-x", "0deg");
                card.style.setProperty("--tilt-y", "0deg");
                card.classList.remove("is-pointer-active");
            });
        });
    }

    const flashMessages = document.querySelectorAll(".flash");
    if (!flashMessages.length) {
        return;
    }

    window.setTimeout(() => {
        flashMessages.forEach((message) => {
            message.style.transition = "opacity 0.4s ease";
            message.style.opacity = "0";
        });
    }, 4000);
});
