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

// カレンダー切り替え機能
document.addEventListener("DOMContentLoaded", async function() {
    const $content = document.getElementById('calendar-content');
    const $label = document.getElementById('current-month-label');
    const $prev = document.getElementById('prev-month');
    const $next = document.getElementById('next-month');
    if (!$content || !$label || !$prev || !$next) return;

    try {
        const res = await fetch(new URL('/json/calendar_data.json', window.location));
        if (!res.ok) throw new Error('calendar_data.json fetch failed');
        const calendarData = await res.json();

        const calendars = calendarData.calendars;
        const availableMonths = calendarData.available_months;
        let currentIndex = 0;

        // 初期月の設定
        if (window.initialMonth && availableMonths.includes(window.initialMonth)) {
            currentIndex = availableMonths.indexOf(window.initialMonth);
        } else {
            currentIndex = availableMonths.length - 1; // 最新月
        }

        function updateSelectedDayBorder() {
            if (!window.currentPageDate) return;
            const d = window.currentPageDate; // YYYY-MM-DD
            const monthStr = d.substring(0, 7);
            if (availableMonths[currentIndex] !== monthStr) return;
            const anchors = $content.querySelectorAll('a');
            anchors.forEach(a => {
                if (a.getAttribute('href') === `/dates/${d}.html`) {
                    const td = a.parentElement;
                    const span = document.createElement('span');
                    span.textContent = a.textContent;
                    td.replaceChild(span, a);
                    td.classList.add('selected-day');
                }
            });
        }

        function updateCalendar() {
            const month = availableMonths[currentIndex];
            $content.innerHTML = calendars[month];
            $label.textContent = month.replace('-', '年') + '月';
            $prev.disabled = (currentIndex === 0);
            $next.disabled = (currentIndex === availableMonths.length - 1);
            updateSelectedDayBorder();
        }

        $prev.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateCalendar();
            }
        });
        $next.addEventListener('click', () => {
            if (currentIndex < availableMonths.length - 1) {
                currentIndex++;
                updateCalendar();
            }
        });

        updateCalendar();
    } catch (e) {
        console.error(e);
    }
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
