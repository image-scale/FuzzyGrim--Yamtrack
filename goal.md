# Goal

## Project
Yamtrack - a Python/Django self-hosted media tracking application.

## Description
A self-hosted media tracker for movies, TV shows, anime, manga, video games, books, comics, and board games. Users can track their media consumption with scores, status (completed, in-progress, planning, paused, dropped), progress, start/end dates, and notes. The application supports multiple users, custom lists, calendar events for upcoming releases, and integrations with external media databases (TMDB, MyAnimeList, IGDB, etc.).

## Core Features
- Track multiple media types: TV shows (with seasons/episodes), movies, anime, manga, games, books, comics, board games
- User tracking: status, score (0-10), progress, start/end dates, notes, repeats
- History tracking via django-simple-history
- Custom user lists with collaboration
- Calendar events for upcoming media releases
- Multiple media providers (TMDB, MAL, IGDB, OpenLibrary, Hardcover, ComicVine, BGG, MangaUpdates)
- Statistics and activity tracking
- Multi-user support with preferences
- Export/import functionality

## Scope
- Core Django apps: config, app (media tracking), users, lists, events, integrations
- ~20 production source files to implement
- ~15 test files to write
- Reproduce core functionality with tests and configuration
