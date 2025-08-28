(analytics/cloud-costs)=
# Cloud Costs Data

In an effort to be transparent about how we use our funds, we publish the amount of money spent each day in cloud compute costs for running mybinder.org.

## Interpreting the data

You can find the data in the [Analytics Archive](https://archive.analytics.mybinder.org) at [cloud-costs.jsonl](https://archive.analytics.mybinder.org/cloud-costs.jsonl). Each line in the file is a JSON object, with the following keys:

1.  **version**

    Currently *1*, will be incremented when the structure of this format changes.

2.  **start_time** and **end_time**

    The start and end of the billing period this item represents. These times are inclusive, and in pacific time observing DST (so PDT or PST). The timezone choice is unfortunate, but unfortunately our cloud provider (Google Cloud Platform) provides detailed billing reports in this timezone only.

3.  **cost**

    The cost of all cloud compute resources used during this time period. This is denominated in US Dollars.

The lines are sorted by `start_time`.
