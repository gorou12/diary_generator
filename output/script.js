document.addEventListener("DOMContentLoaded", function() {
    const toggleButton = document.getElementById("toggle-theme");
    const currentTheme = localStorage.getItem("theme");
    
    if (currentTheme === "dark") {
        document.body.classList.add("dark-mode");
        toggleButton.textContent = "☀️";
    }

    toggleButton.addEventListener("click", function() {
        document.body.classList.toggle("dark-mode");
        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
            toggleButton.textContent = "☀️";
        } else {
            localStorage.setItem("theme", "light");
            toggleButton.textContent = "🌙";
        }
    });
});