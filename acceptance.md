# Acceptance Criteria

## Task 1: Initialize Django project with settings, user model, and core configuration

### Acceptance Criteria
- [ ] Django project structure created with manage.py, config app with settings, urls
- [ ] Custom User model extending AbstractUser with username ordering
- [ ] User model includes preference fields: home_sort, media layout/sort/status preferences for each media type
- [ ] User model includes notification settings and integration token
- [ ] User preference choice enums defined (HomeSortChoices, MediaSortChoices, MediaStatusChoices, LayoutChoices, etc.)
- [ ] User.update_preference() method validates and updates user preferences
- [ ] User.get_enabled_media_types() returns list of enabled media types based on user settings
- [ ] Test settings configured for testing with fakeredis
- [ ] pytest.ini configured for Django test discovery
- [ ] Tests verify User model creation with default preferences
- [ ] Tests verify User.update_preference() validates choices correctly
- [ ] Tests verify User.get_enabled_media_types() returns correct list
