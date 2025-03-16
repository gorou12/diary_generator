document.addEventListener("DOMContentLoaded", function() {
    const toggleButton = document.getElementById("toggle-theme");
    const currentTheme = localStorage.getItem("theme");
    
    
    if (currentTheme === 'dark') {
        document.documentElement.classList.add("dark");
        toggleButton.textContent = "☀️";
    }

    toggleButton.addEventListener("click", function() {
        const currentTheme = localStorage.getItem("theme");
        const html = document.documentElement;
        const isDark = currentTheme === 'dark'
        // html.classList.add("transition-on");
        if (isDark) {
            html.classList.remove("dark");
            localStorage.setItem("theme", "light");
            toggleButton.textContent = "🌙";
        } else {
            html.classList.add("dark");
            localStorage.setItem("theme", "dark");
            toggleButton.textContent = "☀️";
        }

        // setTimeout(() => html.classList.remove('transition-on'), 1000);
    });
});

// リスト絞り込み検索用
function filterList() {
    const input = document.getElementById('searchBox');
    const filter = input.value.toLowerCase();
    const lists = document.querySelectorAll('ul li');

    lists.forEach(function (item) {
        const text = item.textContent.toLowerCase();
        if (text.includes(filter)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}
