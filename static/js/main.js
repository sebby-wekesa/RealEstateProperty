document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("js-ready");

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
