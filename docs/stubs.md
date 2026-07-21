# Stubs

For developing and running tests, simple static stubs are used in place of the live external services.

## Stub data

This stub data exist in a few places depending on the service being stubbed.

For example, the osu api stub data can be found in `common/osu/stubdata/osuapi/`.

## Ephemeral stub data

In addition to the base stub data checked into the repo, it can be helpful to add additional data to mimic new events occuring.

For example adding new osu users and scores to the osu api which can be done in `common/osu/stubdata/osuapi_ephemeral/` which is merged with the base stub data on read by the stub.

## Helper commands

To generate useful stub data, a few commands exist.

`python manage.py addstubuser` adds a new user with randomised stats.

`python manage.py addstubscore <user_id>` adds a new score for a given user by copying an existing base stub data score as a template and randomising it slightly.

`make generate-ephemeral-stub-data` ensures 10 stub users exist and starts a loop that continuously adds scores for them. This is the most useful to simply simulate usage for features that rely on new scores appearing.
