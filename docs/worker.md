# The celery worker

## Task priorities

As a general guide, here are some uses for different task priorities.

| Priority    | Use                          |
| ----------- | ---------------------------- |
| Priority 10 | Time sensitive notifications |
| Priority 9  |                              |
| Priority 8  |                              |
| Priority 7  | Profile updates              |
| Priority 6  |                              |
| Priority 5  | Default                      |
| Priority 4  | Low priority profile updates |
| Priority 3  | Task dispatching tasks       |
| Priority 2  |                              |
| Priority 1  |                              |
| Priority 0  | Background maintenance tasks |
