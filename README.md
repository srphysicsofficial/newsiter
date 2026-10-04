# SR Physics — Vercel + Aiven

## Deploy through GitHub
1. Create a new private personal GitHub repository.
2. Upload all the contents of this github-ready folder into the repository root. app.py, requirements.txt and vercel.json must be at the top level. Do not upload the outer ZIP or the private environment file.
3. Open https://vercel.com/new and import this repository.
4. Framework: Flask. Root Directory: ./ . Leave install/output settings at their defaults. The build command is already configured as python build_assets.py.
5. Before deploying, expand Environment Variables. Import the PRIVATE-VERCEL-ENV.env file supplied OUTSIDE this folder, or paste its entire contents into the environment-variable form. All five variables must be added: DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD, CRON_SECRET, SR_DB_SCHEMA. Select the Production environment. If variables are added after deployment, redeploy.
6. Click Deploy. Open the generated HTTPS URL. Admin is /admin and the password is the ADMIN_PASSWORD value in your private environment file (unchanged from the working local version).
7. Check news, sessions, join requests, paper feedback, and admin create/delete. Redeploy once and confirm records remain. /healthz tests application reachability; /api/news tests database access too.
8. After that succeeds, add srphysics.lk and www.srphysics.lk in Vercel Settings → Domains. At domains.lk, replace the existing GitHub Pages records with the exact DNS records shown by Vercel. Do not change DNS before the new deployment works.

## What stays the same
All HTML, CSS, JavaScript and images are byte-for-byte unchanged. URLs and API response formats are retained. The existing Aiven database and sr_physics_local schema are used, so existing data remains. Do not change SR_DB_SCHEMA if you want those records. The existing single-paper and seven-day deletion rules still apply.

## Production behavior
- Flask exports through app.py using Vercel's Python runtime (3.12).
- build_assets.py copies unchanged frontend files to public/ for Vercel's CDN. It does not connect to the database.
- Tables are initialized on the first API call. Schema initialization is serialized using a PostgreSQL advisory lock.
- Each transaction commits/rolls back and closes its connection; a maximum of two connections per function instance are opened by this adapter. This is NOT a global cap across Vercel instances. Aiven's connection limit still applies under traffic spikes.
- Database failures return a generic retryable HTTP 503 response, without exposing credentials.
- Sessions use HttpOnly, SameSite=Lax, and Secure cookies on Vercel. Credentials come only from environment variables.
- Paper expiry is enforced on API requests. A daily authenticated cron also removes expired records with no visitors. It is not a continuously running one-minute background worker: no-traffic physical deletion can occur at the next daily cron. Expired records are cleaned before the next normal API response.
- No SQLite, JSON storage, local backups or writable local files are required on Vercel.

## Preview deployments
Do not give untrusted preview deployments the live database credentials. To test a trusted preview against Aiven, provide the variables to Preview and use a DIFFERENT SR_DB_SCHEMA such as sr_physics_preview. Preview writes/cleanup would otherwise modify production records. Cron runs in production.

## Local run (optional)
Copy the private env file into this folder as .env, install requirements with pip, then run python run.py. Never commit .env.

## Limits and verification
The package was tested locally; a live Vercel deployment has not been performed. There is no zero-error or unlimited-capacity guarantee. Aiven outages, connection limits and hosting quotas still apply. Vercel Hobby is for personal non-commercial use; a website promoting paid tuition requires an eligible paid plan.

Official references:
- https://vercel.com/docs/frameworks/backend/flask
- https://vercel.com/docs/cron-jobs/manage-cron-jobs
- https://vercel.com/docs/limits/fair-use-guidelines
- https://aiven.io/docs/products/postgresql/concepts/pg-free-tier
