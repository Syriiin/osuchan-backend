# The celery worker

## Task priorities

As a general guide, here are some uses for different task priorities.

Generally higher priority tasks should tend to be shorter so as to not block the worker.

| Priority   | Use                                 |
| ---------- | ----------------------------------- |
| Priority 0 | Time sensitive notifications        |
| Priority 1 | Time sensitive updates              |
| Priority 2 | High priority updates               |
| Priority 3 | Profile updates                     |
| Priority 4 |                                     |
| Priority 5 | Default                             |
| Priority 6 | Low priority profile updates        |
| Priority 7 | Background update dispatching tasks |
| Priority 8 |                                     |
| Priority 9 |                                     |
