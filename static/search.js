document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-bar');
    const searchButton = document.getElementById('search-button');
    const animeContainer = document.getElementById('anime-container3');
    const checkAnimeList = document.getElementById('check-anime-list'); // Checkbox for search
    const loadingOverlay = document.getElementById('loading-overlay');

    animeContainer.innerHTML = '<p id="empty_search">Search for something!</p>';

    // Function to notify reinitialization
    function notifyAddAnime() {
        if (window.reinitialize) {
            window.reinitialize(); // Call the reinitialize function from add_anime.js
        }
    }

    const performSearch = async () => {
        const query = searchInput.value.trim();
        const checkListValue = checkAnimeList.checked ? 'on' : 'off'; // Get checkbox state

        loadingOverlay.style.display = 'flex';
    
        try {
            const response = await fetch(`/search?q=${encodeURIComponent(query)}&check_list=${checkListValue}`);
            const data = await response.json(); // Should be an array now
            console.log('Raw JSON Data:', JSON.stringify(data, null, 2));
            animeContainer.innerHTML = '';
    
            if (data.length === 0) {
                animeContainer.innerHTML = '<p id="empty_search">No results found :(</p>';
                loadingOverlay.style.display = 'none';
                return;
            }
    
            data.forEach(anime => {
                const animeCard = document.createElement('div');    
                animeCard.className = 'anime-card3';
                animeCard.dataset.animeId = anime.id;
                animeCard.innerHTML = `
                    <a href="https://myanimelist.net/anime/${anime.id}" target="_blank">
                        <img src="${anime.image}" alt="${anime.title_default}" class="anime-image">
                    </a>
                    <div class="anime-info">
                        <div class="anime-title">
                            <h3>${anime.title_display}</h3>
                        </div>
                        <ul class="anime-scores">
                            <li><strong>ID:</strong> ${anime.id}</li>
                            <li><strong>Score:</strong> ${anime.score}</li>
                            <li><strong>Year:</strong> ${anime.year}</li>
                            <li><strong>Episodes:</strong> ${anime.episodes}</li>
                            <li><strong>Studio:</strong> ${anime.studio}</li>
                        </ul>
                    </div>
                    <div class="rating-bar">
                        <label for="rating-${anime.id}"></label>
                        <div class="rating-slider">
                            <input type="range" id="rating-${anime.id}" name="rating-${anime.id}" min="0" max="10" step="1" value="0">
                            <span class="rating-value" id="rating-value-${anime.id}">0</span>
                        </div>
                        <label for="status-${anime.id}"></label>
                        <select id="status-${anime.id}" name="status-${anime.id}">
                            <option value="">Select status</option>
                            <option value="completed">Completed</option>
                            <option value="watching">Watching</option>
                            <option value="plan_to_watch">Plan to Watch</option>
                            <option value="dropped">Dropped</option>
                            <option value="on_hold">On Hold</option>
                        </select>
                    </div>
                    <input type="hidden" name="anime_ids" value="${anime.id}">
                `;
                animeContainer.appendChild(animeCard);
    
                // Initialize rating display
                const slider = animeCard.querySelector('.rating-slider input');
                const valueDisplay = animeCard.querySelector('.rating-value');
                valueDisplay.textContent = slider.value;
    
                // Update rating display
                slider.addEventListener('input', (e) => {
                    valueDisplay.textContent = e.target.value;
                });
            });
    
            // Notify add_anime.js of the new cards
            notifyAddAnime();

            loadingOverlay.style.display = 'none';
            
        } catch (error) {
            console.error('Error fetching search results:', error);
        }
    };

    searchButton.addEventListener('click', performSearch);

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});
