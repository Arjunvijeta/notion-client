# Cache System Flowchart

## Complete Cache Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        NOTION CLIENT CACHE SYSTEM                          │
│                     Automatic Performance Optimization                     │
└────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                            READ OPERATIONS
                   (get_page, get_database, get_block_children)
═══════════════════════════════════════════════════════════════════════════

                            ┌──────────────────┐
                            │  User Calls API  │
                            │  e.g.,           │
                            │  get_page("123") │
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Is Caching      │
                            │  Enabled?        │
                            └────┬──────┬──────┘
                                 │      │
                           NO ◄──┘      └──► YES
                            │                 │
                            │                 ▼
                            │        ┌──────────────────┐
                            │        │  Generate        │
                            │        │  Cache Key       │
                            │        │  (resource_id)   │
                            │        └────────┬─────────┘
                            │                 │
                            │                 ▼
                            │        ┌──────────────────┐
                            │        │  Thread Lock     │
                            │        │  Acquire         │
                            │        └────────┬─────────┘
                            │                 │
                            │                 ▼
                            │        ┌──────────────────┐
                            │        │  Check Cache     │
                            │        │  Dictionary      │
                            │        └───┬─────────┬────┘
                            │            │         │
                            │      FOUND │         │ NOT FOUND
                            │            │         │
                            │            ▼         │
                            │   ┌──────────────────┐│
                            │   │  ✓ CACHE HIT     ││
                            │   │  Stats: hits++   ││
                            │   │  Lock Release    ││
                            │   └────────┬─────────┘│
                            │            │          │
                            │            ▼          │
                            │   ┌──────────────────┐│
                            │   │  Return Cached   ││
                            │   │  Data (instant!) ││
                            │   └──────────────────┘│
                            │                       │
                            ▼                       ▼
                   ┌─────────────────────────────────────┐
                   │  ✗ CACHE MISS                       │
                   │  Stats: misses++                    │
                   │  Lock Release                       │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Make HTTP Request to Notion API    │
                   │  • With retry logic                 │
                   │  • With timeout handling            │
                   │  • With error handling              │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Receive Response from Notion       │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  If Caching Enabled:                │
                   │  • Acquire thread lock              │
                   │  • Store in cache with TTL          │
                   │  • Release lock                     │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Return Fresh Data to User          │
                   └─────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                            WRITE OPERATIONS
          (update_page, create_page, append_block_children, etc.)
═══════════════════════════════════════════════════════════════════════════

                            ┌──────────────────┐
                            │  User Calls      │
                            │  Write Operation │
                            │  e.g.,           │
                            │  update_page()   │
                            └────────┬─────────┘
                                     │
                                     ▼
                   ┌─────────────────────────────────────┐
                   │  Make HTTP Request to Notion API    │
                   │  • POST/PATCH/DELETE request        │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Receive Success Response           │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  AUTO-INVALIDATE CACHE              │
                   │  (Smart Invalidation Logic)         │
                   └──────────────────┬──────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │ update_page  │  │ create_page  │  │ append_block │
          │ invalidates: │  │ invalidates: │  │ invalidates: │
          │ • page cache │  │ • parent DB  │  │ • block      │
          │   for ID     │  │   cache      │  │   cache      │
          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   │
                                   ▼
                   ┌─────────────────────────────────────┐
                   │  Acquire Thread Lock                │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Remove Entry from Cache            │
                   │  • Delete from cache dictionary     │
                   │  • Stats: invalidations++           │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Release Thread Lock                │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                   ┌─────────────────────────────────────┐
                   │  Return Success Response to User    │
                   │  (Cache now contains fresh data on  │
                   │   next read)                        │
                   └─────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                        CACHE INVALIDATION RULES
═══════════════════════════════════════════════════════════════════════════

    ┌────────────────────────────────────────────────────────────────┐
    │  Operation                  │  Cache Invalidation              │
    ├────────────────────────────────────────────────────────────────┤
    │  update_page(page_id)       │  → Clear page_cache[page_id]    │
    │  create_page(parent_db_id)  │  → Clear db_cache[parent_db_id] │
    │  append_block_children(id)  │  → Clear blocks_cache[id:*]     │
    │  update_block(block_id)     │  → Clear blocks_cache[block_id] │
    │  delete_block(block_id)     │  → Clear blocks_cache[block_id] │
    │  update_database(db_id)     │  → Clear db_cache[db_id]        │
    └────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                            CACHE LIFECYCLE
═══════════════════════════════════════════════════════════════════════════

    Time: 0s
    ┌────────────────────┐
    │  get_page("123")   │  → API call, cache MISS
    │  Store with TTL    │
    │  TTL: 300s         │
    └────────────────────┘

    Time: 1s
    ┌────────────────────┐
    │  get_page("123")   │  → Cache HIT (instant)
    │  Remaining: 299s   │
    └────────────────────┘

    Time: 150s
    ┌────────────────────┐
    │  get_page("123")   │  → Cache HIT (instant)
    │  Remaining: 150s   │
    └────────────────────┘

    Time: 200s
    ┌────────────────────┐
    │  update_page("123")│  → API call, auto-invalidate
    │  Cache cleared!    │
    └────────────────────┘

    Time: 201s
    ┌────────────────────┐
    │  get_page("123")   │  → Cache MISS (fresh data)
    │  Store with TTL    │
    │  TTL: 300s         │
    └────────────────────┘

    Time: 301s + 300s = 601s (no updates occurred)
    ┌────────────────────┐
    │  get_page("123")   │  → Cache MISS (TTL expired)
    │  Store with TTL    │  → Fresh data from API
    │  TTL: 300s         │
    └────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                        THREAD SAFETY MECHANISM
═══════════════════════════════════════════════════════════════════════════

    Thread 1                    Cache Lock                Thread 2
       │                            │                         │
       │──── get_page("123") ──────►│                         │
       │                            │                         │
       │◄─── Acquire Lock ──────────┤                         │
       │                            │                         │
       │     Check cache            │                         │
       │                            │                         │
       │                            │◄──── get_page("456") ───┤
       │                            │                         │
       │                            │─── Wait for lock ──────►│
       │                            │                         │
       │──── Release Lock ─────────►│                         │
       │                            │                         │
       │                            │◄──── Acquire Lock ──────┤
       │                            │                         │
       │                            │     Check cache         │
       │                            │                         │
       │                            │─── Release Lock ───────►│


═══════════════════════════════════════════════════════════════════════════
                        CACHE STATISTICS TRACKING
═══════════════════════════════════════════════════════════════════════════

    Every Cache Operation Updates Stats:

    ┌─────────────────────────────────────────────┐
    │  Cache Hit    → stats['hits'] += 1          │
    │  Cache Miss   → stats['misses'] += 1        │
    │  Invalidation → stats['invalidations'] += 1 │
    └─────────────────────────────────────────────┘

    Calculate Hit Rate:

    hit_rate = (hits / (hits + misses)) * 100

    Example Output from get_cache_stats():
    {
        'enabled': True,
        'hits': 245,
        'misses': 68,
        'invalidations': 12,
        'total_requests': 313,
        'hit_rate_percent': 78.27,
        'cache_sizes': {
            'pages': 15,
            'blocks': 32,
            'databases': 4
        }
    }
```

## Real-World Example Flow

```
Scenario: Agent reads a page multiple times, then updates it

Step 1: First Read
  get_page("job_123")
  → Cache MISS
  → API call (200ms)
  → Store in cache with 5-min TTL
  → Return data

Step 2: Second Read (2 seconds later)
  get_page("job_123")
  → Cache HIT!
  → Return from cache (<1ms)
  → 200x faster!

Step 3: Third Read (10 seconds later)
  get_page("job_123")
  → Cache HIT!
  → Return from cache (<1ms)

Step 4: Update Operation
  update_page("job_123", {"Status": "Applied"})
  → API call (250ms)
  → Success!
  → Auto-invalidate cache for "job_123"
  → Cache is now empty for this page

Step 5: Fourth Read (immediately after update)
  get_page("job_123")
  → Cache MISS (was invalidated)
  → API call (200ms) - gets fresh data
  → Store in cache with 5-min TTL
  → Return data

Result: 3 API calls instead of 5 (40% reduction)
        Total time: ~650ms instead of ~1000ms (35% faster)
```

## Key Design Principles

1. **Transparency**: Cache works automatically, no code changes needed
2. **Safety**: Write operations always invalidate to ensure data consistency
3. **Performance**: Significant reduction in API calls and response time
4. **Thread-Safe**: Lock mechanism prevents race conditions
5. **Observable**: Statistics provide insight into cache effectiveness
6. **Configurable**: TTLs and cache size can be tuned per use case
7. **Graceful**: Degrades to no caching if library not installed
