# Your Anime List
### Description: web application that uses the MyAnimeList service to give the user personalized recommendations.

Current link: https://your-anime-list.onrender.com/
(The server where it's hosted takes a while to startup since it's a free tier)

"Your Anime List" is a an application that provides personalized anime recommendations using a vector-based algorithm. It leverages two databases: one for managing user data and another for fetching detailed anime information. The app offers a variety of features, including the ability to merge your anime lists with friends, limit recommendations by specific anime IDs or custom parameters, access in-depth statistics, and search the anime database using advanced filters. Let’s explore each feature in detail.

### The algorithm:

Steps of the Algorithm:

1) Extracting User Data:
The algorithm first gathers all anime IDs from the user's watch history, including completed, dropped, watching, and on-hold anime. This ensures the algorithm avoids recommending anime that the user has already interacted with.
        
2) Analyzing User Preferences:
It then analyzes the user's preferences based on the anime they have completed.
The preferences are built by looking at key features like genres, themes, studios, episode counts, and release years. Scores given by the user are used to weigh the importance of these features.
The algorithm also allows filtering by recent anime preferences if specified.

3) Computing Preference Vectors:
Based on the user's completed anime, it generates genre and theme preference vectors. These vectors are essentially a numerical representation of how much the user prefers certain genres or themes.

 4) Database Query for Recommendations:
The algorithm queries the anime database to fetch anime that match the user's preferences. For each potential recommendation, it compares the genre and theme vectors with those of the anime in the database.
It excludes certain types of anime (like commercials or specials) and filters out content based on user settings (e.g., excluding NSFW).

5) Calculating Similarity Scores:
It computes a similarity score between the user's preferences and each anime using cosine similarity. This score indicates how closely the anime matches the user's genre and theme preferences. The similarity score is further adjusted based on other factors like the studio, demographic, and the number of episodes.

6) Applying Additional Weights:
The algorithm applies additional weights to account for factors such as:
    - Year similarity: How close the anime's release year is to the user's preferred year range.
    - Studio similarity: Whether the user has liked other anime from the same studio.
    - Demographic similarity: Whether the anime belongs to demographics the user prefers.
    - Episode similarity: Whether the number of episodes is close to the user's preference.
    - Movie prioritization: Movies are handled separately to ensure they appear prominently in the recommendations.

7) Returning Recommendations:
After calculating and sorting the similarity scores, the algorithm returns two sets of recommendations:
Regular anime: A list of TV shows or longer-form content.
 Movies: A separate list of movie recommendations.
 
### Features of the recommendations page:
 
1) Anime Selection for Algorithm Input:
This feature allows you to manually select certain anime IDs as input for the recommendation algorithm. You provide a comma-separated list of anime IDs that you've completed watching. These IDs are then used to guide the algorithm to suggest similar animes, while excluding the ones you've already selected. This gives you more control over the recommendations by letting you specify exactly which animes to base the recommendations on, helping you avoid repetitive suggestions from your own watch history.

2) Merging User Lists:
When you want to see recommendations based on both your anime list and your friends', this feature comes into play. You can input the user IDs of your friends, and the system will retrieve their anime lists from the database. These lists are then combined with yours, and duplicates are filtered out to ensure each anime only appears once. The algorithm then uses the merged list to provide recommendations, making it easy to discover new shows that both you and your friends might enjoy. It's a great way to find common interests or explore animes that your friends have already watched and liked.

3) Limiting Anime List for Algorithm Input:
If you want recommendations to be based only on your recent anime-watching habits, this feature lets you limit the input to your last watched animes. You specify how many of your most recent animes should be considered by the algorithm, ensuring that your recommendations are fresh and relevant to your current preferences. This is useful if your tastes have changed or if you want the algorithm to focus more on what you've been watching lately rather than your entire watch history.

4) List Update from MyAnimeList (MAL):
This feature allows you to sync your anime list with MyAnimeList (MAL), ensuring that the list stored locally in the application is always up to date. It pulls in your latest watched animes, ratings, and statuses from MAL, and updates both the local database and your session data. This way, any changes you make on MAL—such as finishing a series or dropping an anime—are reflected in the app. The updated list is then fed into the recommendation algorithm, so the suggestions remain accurate and relevant to your latest activity. It also saves your anime list in the app's database, so your watch history is always synchronized.

### Features of the search page:

The search functionality on this page is powered by JavaScript and operates by making a GET request to the server when a user submits a search query. Here's a detailed breakdown of how it works:

1) User Input: The search process starts when the user types a query into the search bar and submits it. The query can include filters like studio, score, number of episodes, year, or anime ID, and the user can sort the results by score or year, either in ascending or descending order.

2) GET Request: When the user submits the search form, JavaScript captures the query and sends a GET request to the server. This request includes the search query and any active filters. The request is sent to a specific search endpoint on the server.

3) Filters: The query can include a variety of filters, such as:
    - Studio: Filters results based on the studio name (e.g., "studio
        ").
    - Score: Allows the user to filter animes by their score, including ranges like score:>7 or score:7.
    - Episodes: Searches for animes with a specific number of episodes (e.g., episodes:12).
    - Year: Filters animes by the year they were released (e.g., year:2015).
    - Anime ID: If the user knows a specific anime ID, they can search directly using that (e.g., id:12345).
    - Sorting: The query also supports sorting by score or year in either ascending or descending order (e.g., asc:scores or desc:year).

4) Server-Side Processing: On the server, the search query is processed. The server extracts the various filters and conditions from the query string using regular expressions. It then searches through a database or dataset of animes, matching animes based on the given criteria.

5) Filter Application:
If no ID filter is provided, the server checks the query against the anime’s title (both the original and English versions).
Studio filters are applied by matching the studio’s name with what the user has entered.
Score, episode count, and year filters are applied using the conditions in the query.
The server also checks if the user has watched the anime (based on session data), and can exclude already-watched animes from the results if specified.

6) Sorting and Limiting Results: Once the server has identified the animes that match the search criteria, it applies any sorting options requested by the user (e.g., sort by year or score). Finally, the server limits the results to a maximum of 50 animes to ensure fast response times.

7) Response and Display: The server sends the filtered and sorted list of animes back to the JavaScript in the form of a JSON response. The JavaScript then dynamically creates anime cards from the response data and displays them on the search results page.

### System for changing status and ratings within the page:

1) User Interaction: The user interacts with the rating and status features through the interface on the page. This typically involves selecting a rating and status for an anime from a list of completed animes that the user has interacted with but hasn't rated yet.

2) JavaScript Interaction: When the user submits their ratings and status updates, JavaScript captures this data from the form. It retrieves the selected anime IDs, ratings, and statuses from the form fields.

3) Sending Data: The JavaScript then sends this data to the server using a POST request. This request includes:

    - A list of anime IDs that the user has rated or updated.
    - The corresponding ratings and statuses for each anime.
    - A flag indicating whether the updates should be saved to the top or not (to change the local list).

4) Server Processing (POST Request):

    - Authentication Check: The server first checks if the user is authenticated by verifying the presence of an access token in the session. If the user is not authenticated, they are redirected to the login page.
    - Data Handling: The server retrieves the current anime list from the session. It processes each anime ID in the request, updating the rating and status as follows:
    - New Animes: For animes that are not already in the list, the server adds them with the provided rating and status. It also records the update time if specified.
    - Existing Animes: For animes already in the list, the server updates their rating and status. If the rating is not zero, it updates both the rating and status. If only a rating is provided, it sets the status to 'completed' by default.
    - Update Confirmation: The server updates the session with the new anime list and responds to the JavaScript with a confirmation message indicating that the update was successful.

### Flask

This app was made using flask and just raw html, css and javascript.
