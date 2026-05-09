# Acceptance Criteria

## Task 1: Initialize Django project with settings, user model, and core configuration

### Acceptance Criteria
- [x] Django project structure created with manage.py, config app with settings, urls
- [x] Custom User model extending AbstractUser with username ordering
- [x] User model includes preference fields: home_sort, media layout/sort/status preferences for each media type
- [x] User model includes notification settings and integration token
- [x] User preference choice enums defined (HomeSortChoices, MediaSortChoices, MediaStatusChoices, LayoutChoices, etc.)
- [x] User.update_preference() method validates and updates user preferences
- [x] User.get_enabled_media_types() returns list of enabled media types based on user settings
- [x] Test settings configured for testing with fakeredis
- [x] pytest.ini configured for Django test discovery
- [x] Tests verify User model creation with default preferences
- [x] Tests verify User.update_preference() validates choices correctly
- [x] Tests verify User.get_enabled_media_types() returns correct list

## Task 2: Implement core media tracking models

### Acceptance Criteria
- [x] Sources enum defined with values: tmdb, mal, mangaupdates, igdb, openlibrary, hardcover, comicvine, bgg, manual
- [x] MediaTypes enum moved to app module with values: tv, season, episode, movie, anime, manga, game, book, comic, boardgame
- [x] Item model stores media metadata: media_id, source, media_type, title, image, season_number, episode_number
- [x] Item model has unique constraints for media_id/source/media_type combinations
- [x] Item model has generate_manual_id() class method returning UUID
- [x] Status enum defined with values: Completed, In progress, Planning, Paused, Dropped
- [x] Media abstract model with fields: item, user, score (0-10 decimal), progress, status, start_date, end_date, notes, created_at
- [x] Media model validates score between 0 and 10 with 1 decimal place
- [x] Media.formatted_score property returns int for 0/10, decimal otherwise
- [x] Media.increase_progress() and decrease_progress() methods update progress by 1
- [x] Tests verify Item creation and unique constraint behavior
- [x] Tests verify Media model field validation (score range)
- [x] Tests verify Media progress methods work correctly

## Task 3: Implement specific media type models

### Acceptance Criteria
- [x] Movie model extends Media with basic tracking
- [x] Anime model extends Media with episode tracking
- [x] Manga model extends Media with chapter tracking
- [x] Game model extends Media with playtime tracking in minutes
- [x] Game.formatted_progress returns time in "Xh YYmin" format (e.g. "2h 30min", "45min")
- [x] Game.increase_progress() adds 30 minutes, decrease_progress() subtracts 30 minutes
- [x] Book model extends Media with page/chapter tracking
- [x] Comic model extends Media with issue tracking
- [x] BoardGame model extends Media with plays tracking
- [x] All models can be saved and retrieved from database
- [x] Tests verify Game playtime formatting works correctly
- [x] Tests verify Game progress methods add/subtract 30 minutes
- [x] Tests verify each model type can be created and persisted

## Task 4: Implement TV/Season/Episode models

### Acceptance Criteria
- [x] TV model extends Media with relationship to seasons
- [x] Season model extends Media with relationship to TV show and episodes
- [x] Episode model stores episode tracking data with relationship to season
- [x] TV.progress property aggregates episode count from all non-zero seasons
- [x] Season.progress property returns highest watched episode number
- [x] TV/Season have unique constraints per user
- [x] Hierarchical relationships: TV -> Seasons -> Episodes
- [x] Tests verify TV progress aggregation across seasons
- [x] Tests verify Season progress returns correct episode number
- [x] Tests verify model relationships are correctly established

## Task 5: Implement helper utilities

### Acceptance Criteria
- [x] minutes_to_hhmm() function converts minutes to "Xh YYmin" format
- [x] format_search_response() formats paginated search results
- [x] Create app/helpers.py module for utility functions
- [x] Tests verify minutes_to_hhmm formatting for various inputs
- [x] Tests verify search response formatting
