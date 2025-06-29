# The celery worker

## Task priorities

As a general guide, here are some uses for different task priorities.

Generally higher priority tasks should tend to be shorter so as to not block the worker.

| Priority    | Use                                 |
| ----------- | ----------------------------------- |
| Priority 10 | Time sensitive notifications        |
| Priority 9  |                                     |
| Priority 8  | Time sensitive updates              |
| Priority 7  | Profile updates                     |
| Priority 6  |                                     |
| Priority 5  | Default                             |
| Priority 4  | Low priority profile updates        |
| Priority 3  | Background update dispatching tasks |
| Priority 2  |                                     |
| Priority 1  |                                     |
| Priority 0  | Background maintenance tasks        |
