# osu!chan architecture

## Code style

- There should be a clear direction of dependency in apps such that circular dependencies are impossible.
- In general, prefer explicit to implicit
  - Rely less on magic framework features and more on concrete parameters passed to straightforward functions
  - DRY still applies, but only for basic cases (ie. extracting common function bodies), not metaprogramming, *args/**kwargs etc...
- No truthy/falsy, always unambiguous conditionals (eg. `is not None`, `== 0`, `len(x) > 0`)
  - plain `if variable:` is fine only if `variable` is a boolean
- Minimal model default values, explicitly set at instance creation is better
- Names should not be abbreviated (minigame_score, not ms), even in iterators except where there is a conflict
- All models, tasks, and services should have a very brief docstring, details only when there is unexpected nuance
- NamedTuple subclasses should be used for DTOs when passing data to self contained logic modules where mutability is not needed
- Explicit type hints should be used for all function parameters, return types, and class members

## App structure

3 entrypoints:
    - `views.py`
    - `tasks.py`
    - `management/commands/...`

`services.py` hold mutations, transaction wrapped if non-trivial, _asserting_ valid inputs before applying changes, parameters can be model instances or ids
`views.py` validate parameters and state such that it not invoke services for mutations with parameters (save for in race conditions)
    - TODO: consider extracting queries into models or a queries.py layer
`tasks.py` are triggered by schedule or on the back of other mutations in services, parameters should be primitives
`models.py` hold ORM models and query helpers, no mutations should exist
`management/commands/...` should call services for any mutations
