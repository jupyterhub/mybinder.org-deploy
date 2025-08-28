(analytics/events-archive)=
# The Analytics Events Archive

BinderHub emits an event each time a repository is launched. They are recorded as JSON, and made available to the public at [archive.analytics.mybinder.org](https://archive.analytics.mybinder.org).

This page describes what is available in the Events Archive & how to interpret it.

## File format

All data files are in [jsonl](https://jsonlines.org/) format. Each line, delimited by a `\n` is a is a well formed JSON object. These files can be read / written in a streaming fashion, one line at a time, without having to read the entire file into memory.

## Launch data by date

For each day since we started keeping track (2018-11-03), there is a file named `events-<YYYY>-<MM>-<DD>.jsonl` that contains data for all the launches performed by mybinder.org on that date. All timestamps and dates are in [UTC](https://en.wikipedia.org/wiki/Coordinated_Universal_Time).

Each line is a JSON object that conforms to [this JSON Schema](https://github.com/jupyterhub/binderhub/blob/HEAD/binderhub/event-schemas/launch.json). A description of these fields is provided below.

1.  **schema** and **version**

    Currently set to `binderhub.jupyter.org/launch` and `1` respectively. These identify the kind of event this is (a launch event from BinderHub) and the current version of the event schema. This lets us evolve the format of the events emitted without breaking existing analytics code. New versions of the launch schema may add additional fields, or change meanings of current ones. We will definitely add other events that are available here too -for example, successful builds.

    Your analytics code **must** make sure the event you are parsing has the schema and version you are expecting before proceeding. If you don\'t do this, your code might fail in unexpected ways in the future.

2.  **timestamp**

    ISO8601 formatted timestamp when the event was emitted. These are rounded down to the closest minute. The lines in the file are ordered by timestamp, starting at the earliest.

3.  **provider**

    Where the launched repository was hosted. Current options are `GitHub`, `GitLab` and `Git`.

4.  **spec**

    Specification identifying the repository / commit immutably & uniquely in the provider.

    For GitHub, it is `<repo>/<commit-spec>`. Example would be `yuvipanda/example-requirements/HEAD`. For GitLab, it is `<repo>/<commit-spec>`, except `repo` is URL escaped. For raw Git repositories, it is `<repo-url>/<commit-spec>`. `repo-url` is full URL escaped to the repo and `commit-spec` is a full commit hash.

5.  **status**

    Wether the launch succeeded (`success`) or failed (`failure`). Currently only successful launches are recorded.

### Example code

Some popular ways of reading this event data into a useful data structure are provided here.

#### `pandas`

``` python
import pandas as pd
df = pd.read_json("https://archive.analytics.mybinder.org/events-2018-11-05.jsonl", lines=True)
df
```

#### Plain Python

``` python
import requests
import json

response = requests.get("https://archive.analytics.mybinder.org/events-2018-11-05.jsonl")
data = [json.loads(l) for l in response.iter_lines()]
```

## `index.jsonl`

The [index.jsonl](https://archive.analytics.mybinder.org/index.jsonl) file lists all the dates an event archive is available for. The following fields are present for each line:

1.  **date**

    The UTC date the event archive is for

2.  **name**

    The name of the file containing the events. This is a relative path - since we got the `index.jsonl` file from [https://archive.analytics.mybinder.org]{.title-ref}, that is the base URL used to resolve these. For example when `name` is `events-2018-11-05.jsonl`, the full URL to the file is `https://archive.analytics.mybinder.org/events-2018-11-05.jsonl`.

3.  **count**

    Total number of events in the file.
