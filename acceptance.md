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

## Task 6: Implement MediaManager for querying media lists

### Acceptance Criteria
- [x] MediaManager class created as a custom Django manager
- [x] get_media_list() method filters by user, media_type, status, with optional search
- [x] get_media_list() annotates with repeat count and filters to latest entry per item
- [x] _apply_prefetch_related() prefetches seasons/episodes for TV and Season types
- [x] _sort_media_list() sorts by various fields (title, score, progress, dates)
- [x] _sort_tv_media_list() handles TV-specific sorting (aggregates from seasons)
- [x] _sort_season_media_list() handles Season-specific sorting (aggregates from episodes)
- [x] _sort_generic_media_list() handles date fields with nulls_last
- [x] BasicMedia model created to attach MediaManager
- [x] Tests verify get_media_list() returns correct filtered results
- [x] Tests verify sorting by different fields works correctly
- [x] Tests verify repeat annotation shows correct count

## Task 7: Implement custom lists feature

### Acceptance Criteria
- [x] Create lists app with models.py
- [x] CustomList model with name, description, owner (ForeignKey to User)
- [x] CustomList has collaborators ManyToMany field to User
- [x] CustomList has items ManyToMany field to Item through CustomListItem
- [x] CustomList.user_can_view() checks if user is owner or collaborator
- [x] CustomList.user_can_edit() checks if user is owner or collaborator
- [x] CustomList.user_can_delete() checks if user is owner
- [x] CustomListItem model with item, custom_list, date_added fields
- [x] CustomListItem has unique constraint on item+custom_list
- [x] CustomListManager.get_user_lists() returns owned or collaborated lists
- [x] CustomListItemManager.get_last_added_date() returns latest date_added
- [x] Tests verify CustomList creation and permissions
- [x] Tests verify CustomListItem unique constraint
- [x] Tests verify manager methods return correct results

## Task 8: Implement calendar events

### Acceptance Criteria
- [x] Create events app with models.py
- [x] Event model with item (ForeignKey), content_number, datetime, notification_sent
- [x] Event has unique constraints for item+content_number combinations
- [x] EventManager.get_user_events() returns events for user's tracked media in date range
- [x] SentinelDatetime class for events without specific time
- [x] Event.is_sentinel_time property checks if datetime is sentinel
- [x] Event.readable_content_number property formats content number
- [x] Tests verify Event creation and unique constraints
- [x] Tests verify EventManager returns filtered events
- [x] Tests verify sentinel time detection

## Task 9: Implement statistics functionality

### Acceptance Criteria
- [x] Create app/statistics.py module
- [x] get_user_media() returns all media for user in date range with counts
- [x] get_media_type_distribution() formats data for pie chart
- [x] get_status_distribution() returns status breakdown per media type
- [x] get_score_distribution() returns score histogram and average
- [x] get_timeline() organizes media by month-year
- [x] calculate_streaks() computes current and longest activity streaks
- [x] Tests verify media retrieval and counting
- [x] Tests verify distribution calculations
- [x] Tests verify streak calculation

## Task 10: Implement provider service layer

### Acceptance Criteria
- [x] Create app/providers/ package with __init__.py and services.py
- [x] ProviderAPIError exception class for API errors
- [x] api_request() function for HTTP requests with timeout and error handling
- [x] get_media_metadata() dispatcher routes to appropriate provider
- [x] search() dispatcher routes search queries to appropriate provider
- [x] Tests verify api_request handles errors correctly
- [x] Tests verify dispatchers route to correct providers

## Task 15: Implement history processing

### Acceptance Criteria
- [x] Create app/config.py module with MEDIA_TYPE_CONFIG and STATUS_CONFIG
- [x] get_verb() returns present/past tense verb for media type (watch, read, play)
- [x] get_unit() returns measurement unit for media type (Episode, Chapter, Page)
- [x] Create app/templatetags/ package with datetime_format filter
- [x] Create app/history_processor.py module
- [x] process_history_entries() processes historical records into timeline entries
- [x] format_description() generates human-readable change descriptions
- [x] Status transitions generate natural language (e.g., "Currently watching", "Finished reading")
- [x] Progress changes format appropriately per media type (playtime for games, pages for books)
- [x] Tests verify get_verb and get_unit cover all media types
- [x] Tests verify format_description for status, score, progress, notes changes
