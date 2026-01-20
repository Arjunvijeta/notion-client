# Notion Client

A robust, production-ready Python client for the Notion API with automatic retries, intelligent caching, and comprehensive error handling. Supports the latest Notion API version (2025-09-03) including data sources and advanced page management.

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/Arjunvijeta/notion-client.git
cd notion-client

# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Dependencies

Core dependencies (automatically installed):

```bash
requests>=2.31.0
urllib3>=2.0.0
cachetools>=5.3.0
```

Development dependencies (optional):

```bash
pip install -r requirements-dev.txt
```

## Quick Start

```python
from notion_client import NotionClient

# Simple usage
client = NotionClient(api_key="your_key")
databases = client.get_all_databases()

# Production-ready with context manager
with NotionClient(api_key="your_key") as client:
    page = client.get_page("page_id")
    data_source = client.get_data_source("data_source_id")
```

## Understanding Notion's Object Hierarchy

Notion organizes content in a hierarchical structure. Understanding this is crucial for effective API usage:

### Core Object Types

```
Workspace (Root)
│
├── Page
│   ├── Properties (only "title" for standalone pages)
│   └── Blocks (content)
│       ├── Paragraph
│       ├── Heading
│       ├── Code
│       ├── Child Page
│       └── Child Data Source
│
└── Data Source (formerly "Database")
    ├── Schema (property definitions: title, text, select, date, etc.)
    ├── Templates (optional page templates)
    └── Entries (collection of pages)
        └── Entry (Page)
            ├── Properties (must match schema)
            └── Blocks (page content)
```

### Key Concepts

1. **Page**: The fundamental content unit in Notion
   - Standalone pages have simple properties (mainly "title")
   - Data source entries are pages with rich, structured properties
   - Every page has a unique ID and URL
   - Pages can contain blocks (content) and child pages/data sources

2. **Data Source** (formerly Database): A structured collection of pages
   - Defines a schema (property types and configurations)
   - Each entry/row is a **page** with properties matching the schema
   - Can have templates for consistent page creation
   - Query with filters and sorts for specific entries

3. **Block**: Content units within pages
   - Types: paragraph, heading, list, code, image, child_page, child_database, etc.
   - Blocks can be nested (e.g., lists with sub-items)
   - Use `get_block_children(page_id)` to fetch page content

4. **Properties**: Structured data fields
   - **Simple properties** (standalone pages): mainly "title"
   - **Rich properties** (data source entries): title, text, number, select, multi-select, date, checkbox, url, email, phone, relation, etc.
   - Property values must match the schema when creating/updating data source entries

### Important Relationships

- **Every data source entry is a page**: Clicking an entry title opens it as a full page
- **Pages have IDs = Block IDs**: A page ID can be used to get its blocks
- **Hierarchy is flexible**: Pages can contain data sources as blocks, data sources can have entries (pages) with nested content
- **Use the right method**:
  - `get_page()` - Get page properties
  - `get_block_children()` - Get page content (blocks)
  - `query_data_source()` - Get entries from a data source with filters

### API Version Update (2025-09-03)

The latest Notion API uses **"data_source"** instead of "database" for structured collections. This client supports both:

- Legacy `database` methods still work for compatibility
- New `data_source` methods provide access to latest features (templates, advanced schemas)
- The terms are often interchangeable in this documentation

## Features

✅ **Flexible Configuration**: Direct parameters or config object  
✅ **Smart Caching**: Automatic response caching with TTL and intelligent invalidation  
✅ **Error Handling**: Custom exceptions (Auth, Validation, RateLimit, NotFound, Conflict)  
✅ **Automatic Retries**: Exponential backoff for transient failures  
✅ **Connection Pooling**: Efficient connection reuse (10 connections)  
✅ **Full Type Hints**: Complete type annotations for better IDE support  
✅ **Context Managers**: Automatic cleanup with `with` statement  
✅ **Comprehensive Logging**: Debug mode for troubleshooting  
✅ **Latest API**: Full support for Notion API 2025-09-03 (data sources, templates)

## Configuration

You can configure the client in three ways:

**1. Direct parameters (recommended):**

```python
client = NotionClient(
    api_key="your_key",
    timeout=30,
    max_retries=3,
    enable_caching=True,
    enable_logging=True
)
```

**2. Config object:**

```python
from notion_client import ClientConfig

config = ClientConfig(
    api_key="your_key",
    notion_version="2025-09-03",     # API version
    timeout=30,                       # Request timeout (seconds)
    max_retries=3,                    # Retry attempts
    retry_backoff_factor=0.3,         # 0.3s, 0.6s, 1.2s...
    enable_logging=False,             # Debug mode
    log_level=logging.INFO,
    enable_caching=True,              # Response caching
    cache_ttl_pages=300,              # Page cache TTL (5 min)
    cache_ttl_blocks=600,             # Block cache TTL (10 min)
    cache_ttl_databases=1800,         # Database cache TTL (30 min)
    cache_ttl_data_sources=1800,      # Data source cache TTL (30 min)
    cache_max_size=100                # Max items per cache
)

client = NotionClient(config)
```

**3. Mix both approaches:**

```python
config = ClientConfig(api_key="your_key")
client = NotionClient(config, enable_logging=True)  # Override specific options
```

## Smart Caching System

Built-in response caching dramatically improves performance by reducing API calls. **Enabled by default**.

### How It Works

- **Read operations** cached with TTL: `get_page()`, `get_data_source()`, `get_block_children()`
- **Write operations** automatically invalidate related caches: `update_page()`, `create_page()`, etc.
- **Thread-safe** with configurable TTL per resource type

### Cache TTLs (Default)

| Resource Type          | TTL    | Reason                            |
| ---------------------- | ------ | --------------------------------- |
| Pages                  | 5 min  | Page properties change moderately |
| Blocks                 | 10 min | Content changes less frequently   |
| Databases/Data Sources | 30 min | Schema rarely changes             |

### Usage

```python
# Enabled by default
client = NotionClient(api_key="key")

# Custom cache settings
client = NotionClient(
    api_key="key",
    enable_caching=True,
    cache_ttl_pages=600  # 10 minutes
)

# Monitor performance
stats = client.get_cache_stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
print(f"Requests saved: {stats['hits']}")

# Clear cache if needed
client.clear_cache()              # Clear all
client.clear_cache("pages")       # Clear specific type
```

### Performance Impact

- **First call**: Hits API (~200ms)
- **Cached calls**: Return instantly (<1ms) until TTL expires
- **After write**: Related cache entries automatically invalidated

### Cache Invalidation Rules

When you modify data, related caches are automatically cleared:

| Operation                 | Invalidates                      |
| ------------------------- | -------------------------------- |
| `update_page()`           | That page + its blocks           |
| `create_page()`           | Parent page/data source          |
| `update_data_source()`    | Data source schema + all entries |
| `append_block_children()` | That block's children            |
| `delete_block()`          | Parent's children + that block   |

**Details**: See [CACHE_FLOWCHART.md](CACHE_FLOWCHART.md) for complete flow diagrams.

**Requirement**: `pip install cachetools`

## API Methods

### Pages

- `get_page(page_id)` - Retrieve page properties
- `create_page(parent_id, properties, ...)` - Create new page or data source entry
- `update_page(page_id, properties)` - Update page properties

### Data Sources (Collections)

- `get_data_source(data_source_id)` - Get data source schema and metadata
- `query_data_source(data_source_id, filter_obj, sorts, ...)` - Query entries with filters/sorts
- `update_data_source(data_source_id, title, properties)` - Update schema
- `get_data_source_templates(data_source_id)` - Get available templates

### Legacy Database Methods (Still Supported)

- `get_database(database_id)` - Alias for get_data_source
- `query_database(database_id, ...)` - Alias for query_data_source
- `create_database(...)` - Create new database
- `update_database(...)` - Alias for update_data_source
- `get_all_databases()` - Search for all databases in workspace
- `get_database_entries(database_id)` - Alias for query_data_source without filters

### Blocks (Content)

- `get_block(block_id)` - Get single block
- `get_block_children(block_id)` - Get all child blocks (page content)
- `append_block_children(block_id, children)` - Add blocks to page
- `update_block(block_id, **kwargs)` - Update block content
- `delete_block(block_id)` - Delete a block

### Search & Users

- `search(query, filter_type, sort)` - Search pages and data sources
- `get_users()` - List all workspace users
- `get_user(user_id)` - Get specific user
- `get_bot_user()` - Get current integration bot user

### Cache Management

- `get_cache_stats()` - View cache performance metrics
- `clear_cache(cache_type)` - Clear all or specific cache type

## Property Helper Functions

Create properly formatted properties for Notion pages:

```python
from notion_client import (
    create_title_property,
    create_text_property,
    create_number_property,
    create_checkbox_property,
    create_select_property,
    create_multi_select_property,
    create_date_property,
    create_url_property,
    create_email_property,
    create_phone_property,
    create_relation_property
)

# Create data source entry with various property types
properties = {
    "Name": create_title_property("Project Title"),
    "Description": create_text_property("Project details"),
    "Priority": create_select_property("High"),
    "Tags": create_multi_select_property(["urgent", "review"]),
    "Completed": create_checkbox_property(False),
    "Count": create_number_property(42),
    "Due Date": create_date_property("2026-01-25"),
    "Date Range": create_date_property("2026-01-20", "2026-01-25"),
    "Website": create_url_property("https://example.com"),
    "Email": create_email_property("contact@example.com"),
    "Phone": create_phone_property("+1234567890"),
    "Related": create_relation_property(["page_id_1", "page_id_2"])
}

client.create_page(
    parent_id="data_source_id",
    parent_type="data_source_id",
    properties=properties
)
```

### Formatter Functions

```python
from notion_client import format_database_title, format_page_title

# Extract titles from API responses
db_title = format_database_title(database_object)
page_title = format_page_title(page_object)
```

## Error Handling

The client provides specific exceptions for different error scenarios:

```python
from notion_client import (
    NotionAPIError,           # Base exception
    NotionAuthenticationError,  # 401 - Invalid API key
    NotionValidationError,      # 400 - Invalid request
    NotionRateLimitError,       # 429 - Rate limit exceeded
    NotionNotFoundError,        # 404 - Resource not found
    NotionConflictError         # 409 - Conflict (e.g., concurrent edit)
)

try:
    page = client.get_page("page_id")
    client.update_page("page_id", properties)

except NotionAuthenticationError as e:
    print(f"Auth failed: {e.message}")
    print("Check your API key and integration permissions")

except NotionValidationError as e:
    print(f"Invalid request: {e.message}")
    print(f"Response: {e.response_data}")

except NotionRateLimitError as e:
    print("Rate limit hit, waiting...")
    time.sleep(60)

except NotionNotFoundError as e:
    print(f"Resource not found: {e.message}")

except NotionConflictError as e:
    print(f"Conflict: {e.message}")

except NotionAPIError as e:
    print(f"API error: {e.message} (code: {e.status_code})")
```

## Usage Examples

### Example 1: List All Data Sources

```python
from notion_client import NotionClient, format_database_title

with NotionClient(api_key="your_key") as client:
    # Get all databases/data sources
    data_sources = client.get_all_databases()

    for ds in data_sources:
        title = format_database_title(ds)
        print(f"📊 {title}")
        print(f"   URL: {ds['url']}")
        print(f"   ID: {ds['id']}\n")
```

### Example 2: Create Data Source Entry

```python
from notion_client import (
    NotionClient,
    create_title_property,
    create_select_property,
    create_date_property,
    create_checkbox_property
)

with NotionClient(api_key="your_key") as client:
    # Create a new job application entry
    new_entry = client.create_page(
        parent_id="data_source_id",
        parent_type="data_source_id",
        properties={
            "Company": create_title_property("Tech Corp"),
            "Position": create_text_property("Senior Engineer"),
            "Status": create_select_property("Applied"),
            "Applied Date": create_date_property("2026-01-20"),
            "Remote": create_checkbox_property(True)
        }
    )

    print(f"✓ Created entry: {new_entry['url']}")
```

### Example 3: Query with Filters and Sorts

```python
# Complex filter: Active jobs from last month
filter_obj = {
    "and": [
        {
            "property": "Status",
            "select": {"equals": "Active"}
        },
        {
            "property": "Applied Date",
            "date": {"after": "2025-12-20"}
        }
    ]
}

sorts = [
    {"property": "Applied Date", "direction": "descending"}
]

results = client.query_data_source(
    "data_source_id",
    filter_obj=filter_obj,
    sorts=sorts
)

print(f"Found {len(results['results'])} matching entries")

for entry in results['results']:
    company = entry['properties']['Company']['title'][0]['text']['content']
    status = entry['properties']['Status']['select']['name']
    print(f"  • {company} - {status}")
```

### Example 4: Batch Operations with Error Handling

```python
from notion_client import NotionClient, NotionAPIError, create_title_property

jobs = [
    {"company": "Company A", "position": "Engineer"},
    {"company": "Company B", "position": "Designer"},
    {"company": "Company C", "position": "Manager"},
]

with NotionClient(api_key="your_key") as client:
    for job in jobs:
        try:
            properties = {
                "Company": create_title_property(job["company"]),
                "Position": create_text_property(job["position"]),
            }

            result = client.create_page(
                parent_id="data_source_id",
                parent_type="data_source_id",
                properties=properties
            )

            print(f"✓ Created: {job['company']}")

        except NotionAPIError as e:
            print(f"✗ Failed {job['company']}: {e.message}")
```

### Example 5: Get Page Content (Blocks)

```python
# Get all blocks from a page
blocks = client.get_block_children("page_id")

for block in blocks['results']:
    block_type = block['type']

    if block_type == 'paragraph':
        # Extract text from paragraph
        texts = [t['plain_text'] for t in block['paragraph']['rich_text']]
        content = ''.join(texts)
        print(f"Paragraph: {content}")

    elif block_type == 'heading_1':
        texts = [t['plain_text'] for t in block['heading_1']['rich_text']]
        print(f"# {''.join(texts)}")

    elif block_type == 'child_database':
        print(f"Child Database: {block['id']}")
```

### Example 6: Create Page with Content

```python
# Create a page with initial content blocks
page = client.create_page(
    parent_id="parent_page_id",
    parent_type="page_id",
    properties={
        "title": create_title_property("Meeting Notes")
    },
    children=[
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "Discussion Points"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "Point 1: API integration"}}]
            }
        }
    ],
    icon={"type": "emoji", "emoji": "📝"}
)
```

### Example 7: Using Templates

```python
# Create data source entry from default template
entry = client.create_page(
    parent_id="data_source_id",
    parent_type="data_source_id",
    properties={
        "Name": create_title_property("Q1 Report")
    },
    template={"type": "default"}  # Use data source's default template
)

# Or use a specific template
entry = client.create_page(
    parent_id="data_source_id",
    parent_type="data_source_id",
    properties={
        "Name": create_title_property("Custom Report")
    },
    template={
        "type": "template_id",
        "template_id": "template_page_id"
    }
)
```

### Example 8: Cache Performance Monitoring

```python
with NotionClient(api_key="your_key", enable_caching=True) as client:
    # First call - hits API
    page1 = client.get_page("page_id")

    # Second call - cached (instant)
    page2 = client.get_page("page_id")

    # Check cache performance
    stats = client.get_cache_stats()
    print(f"Cache hit rate: {stats['hit_rate_percent']}%")
    print(f"API calls saved: {stats['hits']}")
    print(f"Cache sizes: {stats['cache_sizes']}")
```

## Package Structure

```
notion_client/
├── __init__.py          # Package exports
├── client.py            # Main NotionClient implementation
├── config.py            # ClientConfig dataclass
├── exceptions.py        # Custom exception classes
├── helpers.py           # Formatter functions
├── properties.py        # Property creator functions
├── examples.ipynb       # Interactive examples (Jupyter)
├── CACHE_FLOWCHART.md   # Cache system documentation
└── README.md            # This file
```

## Importing

All public APIs are exported from the package root:

```python
from notion_client import (
    # Client
    NotionClient,
    ClientConfig,

    # Exceptions
    NotionAPIError,
    NotionAuthenticationError,
    NotionValidationError,
    NotionRateLimitError,
    NotionNotFoundError,
    NotionConflictError,

    # Formatters
    format_database_title,
    format_page_title,

    # Property creators
    create_title_property,
    create_text_property,
    create_number_property,
    create_checkbox_property,
    create_select_property,
    create_multi_select_property,
    create_date_property,
    create_url_property,
    create_email_property,
    create_phone_property,
    create_relation_property,
)
```

## Troubleshooting

### Authentication Failed (401)

**Problem**: `NotionAuthenticationError: Authentication failed`

**Solutions**:

- Verify API key is correct (starts with `secret_` or `ntn_`)
- Check integration has access to the workspace
- Ensure integration is shared with specific pages/databases you're accessing
- Regenerate API key if needed

### Resource Not Found (404)

**Problem**: `NotionNotFoundError: Resource not found`

**Solutions**:

- Verify page/database/block ID is correct (32-character hex without dashes)
- Ensure integration has access to that specific resource
- Check if resource was deleted
- Share the page/database with your integration

### Validation Error (400)

**Problem**: `NotionValidationError: Validation error`

**Solutions**:

- Check property names match the data source schema exactly (case-sensitive)
- Verify property types match (e.g., don't pass text to a number property)
- Ensure required properties are provided
- Check date format is ISO 8601 (e.g., "2026-01-20")
- Review error response: `e.response_data` for specific validation details

### Rate Limit (429)

**Problem**: `NotionRateLimitError: Rate limit exceeded`

**Solutions**:

- Implement exponential backoff (client does this automatically for retries)
- Add delays between batch operations
- Enable caching to reduce API calls
- Consider upgrading Notion plan for higher rate limits

### Slow Performance

**Solutions**:

- Enable caching: `NotionClient(api_key="key", enable_caching=True)`
- Monitor cache hit rate: `client.get_cache_stats()`
- Increase cache TTLs for static data
- Use batch operations where possible
- Filter queries to return only needed data

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'cachetools'`

**Solution**:

```bash
pip install cachetools
```

Or disable caching:

```python
client = NotionClient(api_key="key", enable_caching=False)
```

## Best Practices

### 1. Use Context Managers

Always use `with` statement for automatic cleanup:

```python
# ✓ Good
with NotionClient(api_key="key") as client:
    page = client.get_page("page_id")

# ✗ Avoid
client = NotionClient(api_key="key")
page = client.get_page("page_id")
# client.close() might be forgotten
```

### 2. Enable Caching for Read-Heavy Workloads

```python
# Good for applications that read more than write
client = NotionClient(
    api_key="key",
    enable_caching=True,
    cache_ttl_pages=600  # Adjust based on your data volatility
)
```

### 3. Handle Errors Specifically

```python
# ✓ Good - catch specific exceptions
try:
    page = client.get_page("page_id")
except NotionNotFoundError:
    print("Page doesn't exist, creating...")
    page = client.create_page(...)
except NotionAuthenticationError:
    print("Check API key")
except NotionAPIError as e:
    print(f"Other error: {e.message}")

# ✗ Avoid - catching all exceptions
try:
    page = client.get_page("page_id")
except Exception:
    pass  # Swallows important errors
```

### 4. Use Type Hints

```python
from typing import Dict, Any, List
from notion_client import NotionClient

def process_data_source(client: NotionClient, ds_id: str) -> List[Dict[str, Any]]:
    results = client.query_data_source(ds_id)
    return results['results']
```

### 5. Batch Operations with Error Handling

```python
# Process multiple items with proper error handling
successful = []
failed = []

for item in items:
    try:
        result = client.create_page(...)
        successful.append(item)
    except NotionAPIError as e:
        failed.append((item, e.message))

print(f"✓ {len(successful)} succeeded, ✗ {len(failed)} failed")
```

### 6. Monitor Cache Performance

```python
# Periodically check cache effectiveness
stats = client.get_cache_stats()
if stats['hit_rate_percent'] < 30:
    print("Cache hit rate low, consider increasing TTLs")
```

### 7. Use Data Source Methods for Collections

```python
# ✓ Prefer data source methods for structured collections
entries = client.query_data_source("ds_id", filter_obj=...)

# ✗ Avoid mixing old database terminology unnecessarily
# (Though both work, data_source is the current API standard)
```

## Contributing

Contributions are welcome! Please ensure:

- Code follows existing style
- Type hints are included
- Error handling is comprehensive
- Documentation is updated

## License

---

**Version**: 1.0.0  
**API Version**: 2025-09-03  
**Last Updated**: January 2026
