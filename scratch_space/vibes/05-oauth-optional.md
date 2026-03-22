# Google OAuth are optional

STATUS: TODO

## Overview

the current webapp configuration includes Google OAuth for authentication and a rate limiting middleware that uses the authenticated user's email to enforce limits.
This is a common pattern for web applications, but it may not be necessary for all projects.
Eg for an internal endpoint that is not exposed to the public but is just an internal service.
