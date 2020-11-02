===============
Events Archiver
===============

**Events Archiver** processes events emitted by BinderHub & makes
them publicly available. It reads from a Google Cloud Storage bucket
populated by `StackDriver export <https://cloud.google.com/logging/docs/export/using_exported_logs>`_,
puts them into a more standard format, and publishes it to another
GCS bucket.

Timestamp resolution reduction
==============================

Publicly published events have timestamps with minute resolution -
second & microsecond information is trimmed. This is a precautionary measure
to protect against possibly de-anonymization attacks in the future.

Running Locally
===============

You can test events archiver locally with:

.. code-block:: bash

   GOOGLE_APPLICATION_CREDENTIALS=secrets/analytics-publisher-auth-key-prod.json \
   python3 images/analytics-publisher/archiver.py \
           --debug \
           --dry-run \
           binderhub binderhub-events-text  \
           mybinder-events-raw-export mybinder-events-archive

The ``--debug`` and ``--dry-run`` options tell the script to print output
to stdout, rather than upload to another GCS bucket.
