document.addEventListener('DOMContentLoaded', () => {
    const sidebarContainer = document.getElementById('anime-container2'); // Sidebar container
    const searchContainer = document.getElementById('anime-container3'); // Search results container
    let modifiedRatings = {}; // Track modified ratings
    let currentIndex = 0; // Track current index for pagination

    const checkBox = document.getElementById('check-update');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Function to initialize sliders for the cards
    function initializeSliders(cards) {
        cards.forEach(card => {
            const slider = card.querySelector('.rating-slider input[type="range"]');
            if (slider) {
                const animeId = slider.id.split('-').pop(); // Extract anime ID
                const valueDisplay = document.getElementById('rating-value-' + animeId);

                slider.addEventListener('input', () => {
                    console.log(`Slider for animeId ${animeId} changed to ${slider.value}`); // Debug log
                    valueDisplay.textContent = slider.value;

                    // Track the modified rating
                    modifiedRatings[animeId] = modifiedRatings[animeId] || {};
                    modifiedRatings[animeId].rating = slider.value;
                });

                // Initialize the value display
                valueDisplay.textContent = slider.value;
            }
        });
    }

    // Function to handle form submission
    function handleFormSubmission(formId, action) {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                
                loadingOverlay.style.display = 'flex';
                const formData = new FormData();

                // Add ratings, statuses, and IDs for both sidebar and search cards
                sidebarContainer.querySelectorAll('.anime-card2').forEach(card => {
                    const animeId = card.getAttribute('data-anime-id');
                    const slider = card.querySelector('.rating-slider input[type="range"]');
                    const status = card.querySelector(`#status-${animeId}`);
                    if (slider) {
                        formData.append(`rating-${animeId}`, slider.value);
                        formData.append('anime_ids', animeId);
                    }
                    if (status) {
                        formData.append(`status-${animeId}`, status.value); // Track the status value
                    }
                });

                searchContainer.querySelectorAll('.anime-card3').forEach(card => {
                    const animeId = card.getAttribute('data-anime-id');
                    const slider = card.querySelector('.rating-slider input[type="range"]');
                    const status = card.querySelector(`#status-${animeId}`);
                    if (slider) {
                        formData.append(`rating-${animeId}`, slider.value);
                        formData.append('anime_ids', animeId);
                    }
                    if (status) {
                        formData.append(`status-${animeId}`, status.value); // Track the status value
                    }
                });
                
                formData.append('check-update', checkBox.checked ? 'checked' : 'unchecked');

                fetch(action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    console.log(`Success for ${formId}:`, data); // Debug log
                    loadingOverlay.style.display = 'none';
                    window.location.reload(); // Reload the page to reflect changes
                })
                .catch(error => {
                    console.error(`Error for ${formId}:`, error); // Debug log
                });
            });
        } else {
            console.error(`Form with id ${formId} not found.`);
        }
    }

    // Function to update pagination button states
    function updateButtonStates(cards) {
        document.getElementById('prev-btn').disabled = currentIndex === 0;
        document.getElementById('next-btn').disabled = currentIndex === cards.length - 1;
    }

    // Function to show the current card
    function showCard(index, cards) {
        cards.forEach((card, i) => {
            card.style.display = i === index ? 'block' : 'none';
        });
        updateButtonStates(cards);
    }

    // Function to show the next card
    function showNextCard(cards) {
        if (currentIndex < cards.length - 1) {
            currentIndex++;
            showCard(currentIndex, cards);
        }
    }

    // Function to show the previous card
    function showPrevCard(cards) {
        if (currentIndex > 0) {
            currentIndex--;
            showCard(currentIndex, cards);
        }
    }

    // Function to reinitialize all sliders and form submission handling
    function reinitialize() {
        initializeSliders(sidebarContainer.querySelectorAll('.anime-card2'));
        initializeSliders(searchContainer.querySelectorAll('.anime-card3'));
    }

    // Initialize sliders and form submission for both sidebar and search results
    reinitialize();

    // Handle form submission for both the sidebar and search form
    handleFormSubmission('rating-form-sidebar', document.getElementById('rating-form-sidebar').action);

    // Pagination controls for both sidebar and search cards combined
    document.getElementById('prev-btn')?.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent page reload
        showPrevCard([...sidebarContainer.querySelectorAll('.anime-card2'), ...searchContainer.querySelectorAll('.anime-card3')]);
    });

    document.getElementById('next-btn')?.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent page reload
        showNextCard([...sidebarContainer.querySelectorAll('.anime-card2'), ...searchContainer.querySelectorAll('.anime-card3')]);
    });

    // Initialize pagination to start with the first card
    if (sidebarContainer.querySelectorAll('.anime-card2').length > 0 || searchContainer.querySelectorAll('.anime-card3').length > 0) {
        showCard(0, [...sidebarContainer.querySelectorAll('.anime-card2'), ...searchContainer.querySelectorAll('.anime-card3')]);
    }
});
