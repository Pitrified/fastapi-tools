#!/bin/bash

# Load resources from CDN to local static folder
# References in docs: docs/guides/webapp_setup.md

mkdir -p static/swagger static/css static/js

# Swagger UI
curl -sL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js" -o static/swagger/swagger-ui-bundle.js
curl -sL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" -o static/swagger/swagger-ui.css

# ReDoc
curl -sL "https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js" -o static/swagger/redoc.standalone.js

# Bulma CSS
curl -sL "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.4/css/bulma.min.css" -o static/css/bulma.min.css

# HTMX JS
curl -sL "https://unpkg.com/htmx.org@1.9.2" -o static/js/htmx.min.js

echo "Swagger, ReDoc, Bulma, and HTMX assets downloaded successfully."
