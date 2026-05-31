document.addEventListener('DOMContentLoaded', () => {
    // Determine the latest timestamp so we know what to fetch
    const newsCards = document.querySelectorAll('.news-card');
    let latestTimestamp = null;
    
    if (newsCards.length > 0) {
        latestTimestamp = newsCards[0].getAttribute('data-timestamp');
    }

    const newsGrid = document.getElementById('newsGrid');

    // Only run polling if we are on the main news page
    if (newsGrid) {
        setInterval(() => {
            if (!latestTimestamp) return;

            fetch(`/api/news/latest?since=${latestTimestamp}`)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        // Update latest timestamp to the newest article's time
                        latestTimestamp = data[0].created_at;

                        data.reverse().forEach(news => {
                            // Create news card element
                            const article = document.createElement('article');
                            article.className = 'news-card highlight-anim';
                            article.setAttribute('data-timestamp', news.created_at);

                            // Lang strings
                            const lang = window.CURRENT_LANG || 'ru';
                            let title = news[`title_${lang}`];
                            let content = news[`content_${lang}`];
                            
                            // Truncate content
                            if (content && content.length > 120) {
                                content = content.substring(0, 120) + '...';
                            }
                            
                            // Format date
                            const dateObj = new Date(news.created_at);
                            const tZDate = dateObj.getFullYear() + "-" + 
                                String(dateObj.getMonth() + 1).padStart(2, '0') + "-" + 
                                String(dateObj.getDate()).padStart(2, '0') + " " + 
                                String(dateObj.getHours()).padStart(2, '0') + ":" + 
                                String(dateObj.getMinutes()).padStart(2, '0');

                            let imageHtml = '';
                            if (news.image_filename) {
                                imageHtml = `
                                <div class="news-image">
                                    <img src="/static/images/uploads/${news.image_filename}" alt="News image">
                                </div>`;
                            } else {
                                imageHtml = `
                                <div class="news-image placeholder">
                                    <span>Жаңалықтар KZ</span>
                                </div>`;
                            }

                            // Build html
                            article.innerHTML = `
                                ${imageHtml}
                                <div class="news-content">
                                    <span class="news-category">${news.category_code}</span>
                                    <h3 class="news-title">${title}</h3>
                                    <p class="news-desc">${content}</p>
                                    <div class="news-meta">
                                        <span class="news-date">${tZDate}</span>
                                        <a href="/news/${news.id}" class="read-more">${window.READ_MORE_TEXT}</a>
                                    </div>
                                </div>
                            `;

                            // Remove no-news text if it exists
                            const noNews = document.querySelector('.no-news');
                            if (noNews) noNews.remove();

                            // Prepend to grid
                            newsGrid.prepend(article);
                        });
                    }
                })
                .catch(err => console.error("Error fetching latest news:", err));
        }, 30000); // 30 seconds
    }
    // Theme Toggle is handled in base.html inline script to prevent FOUC and duplicate listeners.

    // --- Scroll Top & Reading Progress ---
    const scrollTopBtn = document.getElementById('scrollTop');
    const progressBar = document.getElementById('readingProgress');

    window.addEventListener('scroll', () => {
        // Scroll Top visibility
        if (scrollTopBtn) {
            if (window.pageYOffset > 300) {
                scrollTopBtn.classList.add('show');
            } else {
                scrollTopBtn.classList.remove('show');
            }
        }

        // Reading Progress
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        if (progressBar) progressBar.style.width = scrolled + "%";
    });

    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // --- Widgets Data ---
    // Realistic Weather (Simulated for speed, but structure ready for API)
    const updateWeather = () => {
        const weatherWidget = document.getElementById('weatherWidget');
        if (!weatherWidget) return;

        // In real app: fetch from OpenWeatherMap or similar
        setTimeout(() => {
            const temp = Math.floor(Math.random() * (25 - 15) + 15);
            weatherWidget.querySelector('.weather-temp').innerText = `${temp}°C`;
            weatherWidget.querySelector('.weather-desc').innerText = 'Ясно, без осадков';
        }, 1000);
    };

    // Realistic Currency (Using public exchange rate API)
    const updateCurrency = () => {
        const usdEl = document.getElementById('usdKzt');
        if (!usdEl) return;

        fetch('https://open.er-api.com/v6/latest/USD')
            .then(res => res.json())
            .then(data => {
                const kztRate = data.rates.KZT;
                const eurRate = data.rates.EUR;
                document.getElementById('usdKzt').innerText = kztRate.toFixed(2);
                document.getElementById('eurKzt').innerText = (kztRate / eurRate).toFixed(2);
                document.getElementById('rubKzt').innerText = (kztRate / data.rates.RUB).toFixed(2);
                
                // BTC is separate
                return fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT');
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('btcusd').innerText = Math.floor(data.price).toLocaleString();
            })
            .catch(err => {
                console.error("Currency fetch error:", err);
                // Fallback values
                document.getElementById('usdKzt').innerText = '445.50';
                document.getElementById('eurKzt').innerText = '482.20';
            });
    };

    updateWeather();
    updateCurrency();

    // ===== LIVE SEARCH =====
    const searchInput = document.getElementById('liveSearchInput');
    const searchResults = document.getElementById('liveSearchResults');
    let searchTimeout;

    if (searchInput && searchResults) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                searchResults.classList.add('d-none');
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        searchResults.innerHTML = '';
                        if (data.length > 0) {
                            data.forEach(item => {
                                const a = document.createElement('a');
                                a.href = `/news/${item.id}`;
                                a.className = 'dropdown-item py-2 border-bottom';
                                a.innerHTML = `
                                    <div class="fw-bold text-truncate" style="max-width: 250px;">${item.title}</div>
                                    <small class="text-muted">${item.date}</small>
                                `;
                                searchResults.appendChild(a);
                            });
                        } else {
                            const div = document.createElement('div');
                            div.className = 'p-3 text-muted text-center small';
                            div.innerText = 'Нәтиже табылған жоқ';
                            searchResults.appendChild(div);
                        }
                        searchResults.classList.remove('d-none');
                    })
                    .catch(err => console.error("Search error:", err));
            }, 300); // 300ms debounce
        });

        // Hide when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('d-none');
            }
        });
    }
});

// ===== TOAST NOTIFICATIONS =====
window.showToast = function(message, type = 'primary') {
    const toastEl = document.getElementById('liveToast');
    const toastMsg = document.getElementById('toastMessage');
    if (toastEl && toastMsg) {
        toastMsg.innerText = message;
        toastEl.className = `toast align-items-center text-white border-0 bg-${type}`;
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
    }
};
