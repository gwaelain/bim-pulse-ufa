const newsContainer = document.querySelector("#news-feed");

if (newsContainer) {
  fetch("news.json")
    .then(response => {
      if (!response.ok) {
        throw new Error("Не удалось загрузить news.json");
      }
      return response.json();
    })
    .then(news => {
      newsContainer.innerHTML = "";

      news.forEach(item => {
        const card = document.createElement("article");
        card.className = "news-card reveal visible";

        card.innerHTML = `
          <div class="news-card-top">
            <span>${item.tag || "BIM"}</span>
            <time>${formatDate(item.date)}</time>
          </div>

          <h3>${item.title}</h3>
          <p>${item.summary}</p>

          <div class="news-card-bottom">
            <small>${item.source}</small>
            <a href="${item.url}" target="_blank" rel="noopener">Читать</a>
          </div>
        `;

        newsContainer.appendChild(card);
      });
    })
    .catch(error => {
      newsContainer.innerHTML = `
        <article class="news-card">
          <h3>Новости временно недоступны</h3>
          <p>Проверьте файл news.json или подключение к сайту.</p>
        </article>
      `;
      console.error(error);
    });
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}
