// ここから全文検索用
let searchData = [];

// 初回読み込み時にデータを取得
fetch(new URL('/json/search_data.json', window.location))
    .then(response => response.json())
    .then(data => {
        searchData = data;
        console.log("✅ search_data.json を読み込みました");
    });

// 全文検索を実行する関数
function fullTextSearch() {
    const input = document.getElementById('search-box');
    const filter = input.value.toLowerCase();
    const resultArea = document.getElementById('search-results');
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
