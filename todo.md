# Todo

## Plan
Build the Django application incrementally, starting with project configuration and core models. First create the foundational config and user model, then add media tracking models, then extend with lists, events, statistics, and provider integrations. Test each feature independently as it's implemented.

## Tasks
- [x] Task 1: Initialize Django project with settings, user model, and core configuration (config app + users app with custom User model supporting preferences)
- [x] Task 2: Implement core media tracking models - Item, Media base class, and status/source/type enums with tracking capabilities (score, progress, status, dates, notes)
- [x] Task 3: Implement specific media type models (Movie, Anime, Manga, Game, Book, Comic, BoardGame) inheriting from Media with unique behaviors like game playtime formatting
- [x] Task 4: Implement TV/Season/Episode models with hierarchical tracking - seasons belong to TV shows, episodes belong to seasons, with progress aggregation
- [x] Task 5: Implement helper utilities for time formatting and search response formatting
- [x] Task 6: Implement MediaManager for querying media lists with filtering, sorting, and status annotations
- [>] Task 7: Implement custom lists feature - CustomList and CustomListItem models with owner/collaborator permissions
- [ ] Task 8: Implement calendar events - Event model for tracking upcoming media releases with manager for user-specific event queries
- [ ] Task 9: Implement statistics functionality - media distribution, status breakdown, score distribution, timeline, and activity tracking
- [ ] Task 10: Implement provider service layer - API request handling with rate limiting and error handling for external media databases
- [ ] Task 11: Implement TMDB provider for TV shows and movies - search and metadata retrieval
- [ ] Task 12: Implement MAL provider for anime and manga - search and metadata retrieval
- [ ] Task 13: Implement IGDB provider for games and OpenLibrary/Hardcover providers for books
- [ ] Task 14: Implement remaining providers - ComicVine for comics, BoardGameGeek for board games, MangaUpdates for manga
- [ ] Task 15: Implement history processing for tracking changes with django-simple-history integration
- [ ] Task 16: Implement export functionality for backing up user media data to CSV
