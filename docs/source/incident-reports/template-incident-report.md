# Template for reports

# {{ incident date: yyyy-mm-dd }}, {{ incident name }}

## Summary

Quick summary of what user impact was, how long it was, and how we fixed it.

## Timeline

All times in {{ most convenient timezone}}

### {{ yyyy-mm-dd hh:mm }}

Start of incident. First symptoms, possibly how they were identified.

### {{ hh:mm }}

Investigation starts.

### {{ hh:mm }}

More details.

## Lessons learnt

### What went well

List of things that went well. For example,

1. We were alerted to the outage by automated bots before it affected users
2. The staging cluster helped us catch this before it went to prod

### What went wrong

Things that could have gone better. Ideally these should result in concrete
action items that have GitHub issues created for them and linked to under
Action items. For example,

1. We do not record the number of hub spawn errors in a clear and useful way,
   and hence took a long time to find out that was happening.
2. Our culler process needs better logging, since it is somewhat opaque now
   and we do not know why restarting it fixed it.

### Where we got lucky

These are good things that happened to us but not because we had planned for them.
For example,

1. We noticed the outage was going to happen a few minutes before it did because
   we were watching logs for something unrelated.

## Action items

These are only sample subheadings. Every action item should have a GitHub issue
(even a small skeleton of one) attached to it, so these do not get forgotten.

### Process improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]

### Documentation improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]

### Technical improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]
