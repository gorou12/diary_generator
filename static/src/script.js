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

// ここから全文検索用
let searchData = [];

// 初回読み込み時にデータを取得
fetch(new URL('/search_data.json', window.location))
    .then(response => response.json())
    .then(data => {
        searchData = data;
        console.log("✅ search_data.json を読み込みました");
    });

// 全文検索を実行する関数
function fullTextSearch() {
    const input = document.getElementById('searchBox');
    const filter = input.value.toLowerCase();
    const resultArea = document.getElementById('searchResults');
    resultArea.innerHTML = ''; // 検索結果をリセット

    if (filter === '') {
        return; // 空なら結果を表示しない
    }

    let hitCount = 0;

    searchData.forEach(item => {
        const targetText = (item.title + " " + item.content).toLowerCase();
        if (targetText.includes(filter)) {
            hitCount++;
            const resultItem = document.createElement('div');
            resultItem.classList.add('search-result-item');
            resultItem.innerHTML = `
                <a href="${item.url}">${item.date}：${item.title}</a>
                <p>${item.content.substring(0, 100)}...</p>
            `;
            resultArea.appendChild(resultItem);
        }
    });

    if (hitCount === 0) {
        resultArea.innerHTML = '<p>該当する記事が見つかりませんでした。</p>';
    }
}
// ここまで全文検索用