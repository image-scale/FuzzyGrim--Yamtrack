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
- [ ] Sources enum defined with values: tmdb, mal, mangaupdates, igdb, openlibrary, hardcover, comicvine, bgg, manual
- [ ] MediaTypes enum moved to app module with values: tv, season, episode, movie, anime, manga, game, book, comic, boardgame
- [ ] Item model stores media metadata: media_id, source, media_type, title, image, season_number, episode_number
- [ ] Item model has unique constraints for media_id/source/media_type combinations
- [ ] Item model has generate_manual_id() class method returning UUID
- [ ] Status enum defined with values: Completed, In progress, Planning, Paused, Dropped
- [ ] Media abstract model with fields: item, user, score (0-10 decimal), progress, status, start_date, end_date, notes, created_at
- [ ] Media model validates score between 0 and 10 with 1 decimal place
- [ ] Media.formatted_score property returns int for 0/10, decimal otherwise
- [ ] Media.increase_progress() and decrease_progress() methods update progress by 1
- [ ] Tests verify Item creation and unique constraint behavior
- [ ] Tests verify Media model field validation (score range)
- [ ] Tests verify Media progress methods work correctly
