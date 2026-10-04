# Validation report

11 integration tests passed against an embedded PostgreSQL (PGlite) engine through psycopg2. These cover public submissions, admin login/logout, paper replacement and deletion, expiry, stale submissions, news visibility, sessions, private-file blocking, secure cookies, cross-origin rejection, cron authentication, and generic database-unavailable responses.

The static asset build completed; emitted public assets match the supplied frontend bytes. All Python modules compile. Repository contents were checked for the private database password, admin password and session/cron secrets.

The live Aiven connection was previously confirmed working by the user for the localhost version. This environment cannot resolve the Aiven hostname, so no remote database changes or verification were performed here. No Vercel account deployment or CDN routing validation was performed; verify the generated URL before switching DNS. Concurrent multi-instance saturation, load tests and third-party media availability are outside these checks.
