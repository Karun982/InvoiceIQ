(function () {
    const root = document.documentElement;
    const savedTheme = localStorage.getItem("invoiceiq-theme");

    function getPreferredTheme() {
        if (savedTheme) {
            return savedTheme;
        }

        return window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    }

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        localStorage.setItem("invoiceiq-theme", theme);

        document.querySelectorAll("[data-theme-toggle]").forEach(button => {
            button.textContent = theme === "dark" ? "☀" : "☾";
            button.setAttribute(
                "aria-label",
                theme === "dark"
                    ? "Switch to light mode"
                    : "Switch to dark mode"
            );
        });
    }

    applyTheme(getPreferredTheme());

    document.addEventListener("DOMContentLoaded", function () {
        applyTheme(root.getAttribute("data-theme") || getPreferredTheme());

        document.querySelectorAll("[data-theme-toggle]").forEach(button => {
            button.addEventListener("click", function () {
                const current = root.getAttribute("data-theme");
                applyTheme(current === "dark" ? "light" : "dark");
            });
        });
    });
})();