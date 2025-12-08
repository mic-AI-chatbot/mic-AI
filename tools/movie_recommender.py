

import logging
import random
import os
import json
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class AdvancedMovieRecommenderTool(BaseTool):
    """
    An advanced tool for recommending movies based on genre or a favorite movie,
    and providing detailed movie information, including search capabilities.
    """

    def __init__(self, tool_name: str = "MovieRecommender", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.movies_file = os.path.join(self.data_dir, "movies.json")
        self.movies: Dict[str, List[Dict[str, Any]]] = self._load_movies()

    @property
    def description(self) -> str:
        return "Recommends movies by genre or based on a favorite movie, and provides detailed movie information."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["recommend_movie", "get_movie_details", "search_movies"]},
                "genre": {"type": "string", "description": "Genre for recommendation (e.g., 'comedy', 'sci-fi')."},
                "favorite_movie_title": {"type": "string", "description": "Title of a favorite movie to base recommendations on."},
                "title": {"type": "string", "description": "Title of the movie to get details for."},
                "director": {"type": "string", "description": "Director's name to search movies by."},
                "year": {"type": "integer", "description": "Year to search movies by."}
            },
            "required": ["operation"]
        }

    def _load_movies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads movie data from a JSON file or uses a default if not found."""
        if os.path.exists(self.movies_file):
            with open(self.movies_file, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted movies file '{self.movies_file}'. Using default data.")
                    return self._default_movies()
        return self._default_movies()

    def _default_movies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Provides a default set of movies."""
        return {
            "comedy": [
                {"title": "The Grand Budapest Hotel", "year": 2014, "director": "Wes Anderson", "synopsis": "Adventures of Gustave H."},
                {"title": "Booksmart", "year": 2019, "director": "Olivia Wilde", "synopsis": "Two academic superstars realize they should have worked less."},
                {"title": "Paddington 2", "year": 2017, "director": "Paul King", "synopsis": "Paddington picks up odd jobs for Aunt Lucy's birthday."},
            ],
            "sci-fi": [
                {"title": "Blade Runner 2049", "year": 2017, "director": "Denis Villeneuve", "synopsis": "A young blade runner's discovery of a long-buried secret."},
                {"title": "Arrival", "year": 2016, "director": "Denis Villeneuve", "synopsis": "A linguist is recruited to translate alien communications."},
                {"title": "Dune", "year": 2021, "director": "Denis Villeneuve", "synopsis": "Paul Atreides must travel to the most dangerous planet."},
            ],
            "drama": [
                {"title": "The Shawshank Redemption", "year": 1994, "director": "Frank Darabont", "synopsis": "Two imprisoned men bond over a number of years."},
                {"title": "The Godfather", "year": 1972, "director": "Francis Ford Coppola", "synopsis": "The aging patriarch of an organized crime dynasty."},
                {"title": "Parasite", "year": 2019, "director": "Bong Joon-ho", "synopsis": "Greed and class discrimination threaten relationships."},
            ],
            "action": [
                {"title": "Mad Max: Fury Road", "year": 2015, "director": "George Miller", "synopsis": "In a post-apocalyptic wasteland, a woman rebels."},
                {"title": "The Dark Knight", "year": 2008, "director": "Christopher Nolan", "synopsis": "When the Joker wreaks havoc, Batman must fight injustice."},
            ]
        }

    def recommend_movie(self, genre: Optional[str] = None, favorite_movie_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommends a movie. If a favorite movie is provided, it recommends a similar one.
        Otherwise, it recommends from a specified genre or any genre.
        """
        if favorite_movie_title:
            fav_movie_lower = favorite_movie_title.lower()
            fav_genre = None
            for g, movie_list in self.movies.items():
                if any(m["title"].lower() == fav_movie_lower for m in movie_list):
                    fav_genre = g
                    break
            
            if fav_genre:
                eligible_movies = [m for m in self.movies[fav_genre] if m["title"].lower() != fav_movie_lower]
                if eligible_movies:
                    return random.choice(eligible_movies)  # nosec B311
                else:
                    return {"message": f"No other movies found in the same genre as '{favorite_movie_title}'. Recommending from all genres."}

        if genre and genre.lower() in self.movies:
            return random.choice(self.movies[genre.lower()])  # nosec B311
        else:
            all_movies = [movie for sublist in self.movies.values() for movie in sublist]
            return random.choice(all_movies)  # nosec B311

    def get_movie_details(self, title: str) -> Dict[str, Any]:
        """Provides details (year, director, synopsis) for a given movie title."""
        title_lower = title.lower()
        for genre, movie_list in self.movies.items():
            for movie in movie_list:
                if movie["title"].lower() == title_lower:
                    return movie
        raise ValueError(f"Movie '{title}' not found in the database.")

    def search_movies(self, director: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Searches for movies by director or year."""
        results = []
        for genre, movie_list in self.movies.items():
            for movie in movie_list:
                match_director = (director is None) or (movie["director"].lower() == director.lower())
                match_year = (year is None) or (movie["year"] == year)
                if match_director and match_year:
                    results.append(movie)
        return results

    def execute(self, operation: str, **kwargs: Any) -> Any:
        """Executes a movie recommendation or search command."""
        op_map = {
            "recommend_movie": self.recommend_movie,
            "get_movie_details": self.get_movie_details,
            "search_movies": self.search_movies
        }
        if operation not in op_map:
            raise ValueError(f"Invalid operation: {operation}. Supported operations are {list(op_map.keys())}.")
        
        # Filter kwargs for the specific operation
        import inspect
        sig = inspect.signature(op_map[operation])
        op_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        
        return op_map[operation](**op_kwargs)

if __name__ == '__main__':
    print("Demonstrating AdvancedMovieRecommenderTool functionality...")
    temp_dir = "temp_movie_recommender_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    recommender_tool = AdvancedMovieRecommenderTool(data_dir=temp_dir)
    
    # Save default movies to file for persistence demo
    with open(recommender_tool.movies_file, 'w') as f:
        json.dump(recommender_tool._default_movies(), f, indent=2)
    
    try:
        # 1. Recommend a movie based on a favorite
        print("\n--- Recommending based on 'Blade Runner 2049' ---")
        rec1 = recommender_tool.execute(operation="recommend_movie", favorite_movie_title="Blade Runner 2049")
        print(json.dumps(rec1, indent=2))

        # 2. Recommend a movie from a specific genre
        print("\n--- Recommending a drama movie ---")
        rec2 = recommender_tool.execute(operation="recommend_movie", genre="drama")
        print(json.dumps(rec2, indent=2))

        # 3. Get movie details
        print("\n--- Getting details for 'Dune' ---")
        details = recommender_tool.execute(operation="get_movie_details", title="Dune")
        print(json.dumps(details, indent=2))

        # 4. Search movies by director
        print("\n--- Searching for movies by Denis Villeneuve ---")
        search_by_director = recommender_tool.execute(operation="search_movies", director="Denis Villeneuve")
        print(json.dumps(search_by_director, indent=2))

        # 5. Search movies by year
        print("\n--- Searching for movies from 2019 ---")
        search_by_year = recommender_tool.execute(operation="search_movies", year=2019)
        print(json.dumps(search_by_year, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
