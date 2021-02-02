# proxy-patches image

This image is used in the proxy-patches pod to add a custom route to CHP
so that 404s for a non-running container are handled by an nginx container
instead of jupyterhub.

This serves two purposes:

1. reduce load on the Hub (we get *lots* of these 404s)
2. provide a more informative custom error page for the likely event of dead links to deleted Binders than JupyterHub's default

This image does not serve the 404 (a default nginx image does this),
it only makes the API requests to ensure that CHP has the required additional route.
