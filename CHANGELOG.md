# Changelog

All notable changes to the notion_client package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-20

### Added

#### Core Features

- **NotionClient**: Production-ready client with flexible configuration
- **ClientConfig**: Dataclass-based configuration with validation
- **Smart Caching System**: Automatic response caching with TTL and intelligent invalidation
  - Page cache (5 min TTL)
  - Block cache (10 min TTL)
  - Database/Data Source cache (30 min TTL)
  - Thread-safe cache operations
  - Cache statistics and monitoring
- **Connection Pooling**: Efficient HTTP connection reuse (10 connections)
- **Automatic Retries**: Exponential backoff for transient failures
- **Context Manager Support**: Automatic resource cleanup

#### API Support

- **Notion API v2025-09-03**: Full support for latest API version
- **Pages API**: get_page, create_page, update_page
- **Data Sources API**: get_data_source, query_data_source, update_data_source, get_data_source_templates
- **Legacy Database API**: Backward compatibility with database methods
- **Blocks API**: get_block, get_block_children, append_block_children, update_block, delete_block
- **Search API**: search with filters and sorting
- **Users API**: get_users, get_user, get_bot_user

#### Error Handling

- **Custom Exceptions**: NotionAPIError, NotionAuthenticationError, NotionValidationError, NotionRateLimitError, NotionNotFoundError, NotionConflictError
- **Detailed Error Messages**: Status codes, response data, and error codes
- **Graceful Degradation**: Optional dependencies handled gracefully

#### Helper Functions

- **Property Creators**: 11 property creator functions for all Notion property types
  - create_title_property, create_text_property, create_number_property
  - create_checkbox_property, create_select_property, create_multi_select_property
  - create_date_property, create_url_property, create_email_property
  - create_phone_property, create_relation_property
- **Formatters**: format_database_title, format_page_title

#### Documentation

- Comprehensive README with 8 detailed examples
- CACHE_FLOWCHART.md for cache system documentation
- Interactive examples.ipynb for hands-on learning
- Full type hints throughout codebase
- Inline documentation and docstrings

#### Development Infrastructure

- **Test Suite**: Comprehensive unit tests with pytest
  - test_config.py: Configuration validation tests
  - test_exceptions.py: Exception handling tests
  - test_helpers.py: Helper function tests
  - test_properties.py: Property creator tests
  - test_client.py: Client functionality tests
  - conftest.py: Shared fixtures and test configuration
- **Package Distribution**: pyproject.toml for modern Python packaging
- **Type Checking**: py.typed marker for PEP 561 compliance
- **Development Tools**: requirements-dev.txt with testing and linting tools
- **Code Quality**: Black, Ruff, and MyPy configuration
- **CI/CD**: GitHub Actions workflows for automated testing
- **Documentation**: CONTRIBUTING.md for contributor guidelines

### Changed

- N/A (Initial release)

### Deprecated

- N/A (Initial release)

### Removed

- N/A (Initial release)

### Fixed

- N/A (Initial release)

### Security

- API keys validated on initialization
- Secure credential handling
- No credentials in logs by default

---

## [Unreleased]

### Planned

- More integration tests with live API
- Performance benchmarks
- CLI tool for common operations
- Async support with httpx
- Webhook support
- Batch operation optimization

---
