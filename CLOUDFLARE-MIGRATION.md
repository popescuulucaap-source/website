# Gargand on Cloudflare

This repository now includes a Cloudflare Workers + Containers deployment path for the
existing Flask application. The container runs the same `app.py`, Jinja templates,
static assets, and Python dependencies as the current Render service. It is intentionally
separate from the existing Render start command (`gunicorn app:app`) so Render can remain
available as a rollback while Cloudflare is validated.

## Platform and cost

Cloudflare Containers requires the Workers Paid plan. Cloudflare's published plan includes
some container usage, but additional memory, CPU, disk, Worker, Durable Object, and network
usage may be billable. Do not deploy the container unless the account owner has enabled the
plan and accepts its usage charges.

## Cloudflare runtime secrets

In Workers & Pages > `gargand` > Settings > Variables and Secrets, configure the existing
values from the old hosting environment. Do not place their values in GitHub:

- `SESSION_SECRET`
- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI` (set to `https://gargand.popescuulucaap.workers.dev/oauth/callback`)
- `DATABASE_URL` (a working PostgreSQL connection string)
- `GARGAND_BRIDGE_SECRET` and/or `NIGHTFALL_BRIDGE_SECRET`
- Any other provider keys the site currently uses, including the Roblox OAuth and OpenRouter
  keys if those features are enabled.

The Worker passes these runtime bindings into the container. Do not add secret values to
`wrangler.jsonc`, source files, or a GitHub Actions/Workers Build command.

## Database and data integrity

The existing app uses PostgreSQL through `DATABASE_URL`. The database observed during
the previous deployment returned a quota-exceeded error. Moving the web process does not
restore that database. A valid database URL with sufficient quota is required to preserve
persistent accounts, announcements, support tickets, settings, and bot bridge state. Do not
replace it with an empty database unless the data has first been backed up and intentionally
migrated.

## Discord OAuth

Add `https://gargand.popescuulucaap.workers.dev/oauth/callback` to the Discord application's
OAuth2 redirect URLs after the new host is active. If using a custom domain later, add that
domain's matching callback too.

## Discord bot bridge

The live Discord bot process is hosted separately from this web container. Update its
environment on the actual bot host (not just the bot's GitHub repository):

- `GARGAND_WEBSITE_URL=https://gargand.popescuulucaap.workers.dev`
- `GARGAND_BRIDGE_SECRET` equal to the secret configured on the Cloudflare website Worker.

If the old bot uses the `NIGHTFALL_*` aliases, update those aliases consistently. The bridge
secret must match on both sides. Never commit or post the secret in chat.

## Deployment checks

After enabling the Workers Paid plan and configuring secrets, connect Workers Builds for this
repository with install/build command `npm install` and deploy command `npx wrangler deploy`.
Then verify:

1. Container startup succeeds and `/health` returns healthy.
2. Main pages and all `/static/*` assets load.
3. Discord OAuth login/callback succeeds.
4. Existing database-backed pages read and write durable data.
5. Bot heartbeat reaches `/api/bot/heartbeat` and dashboard actions return through the bridge.
6. Test bot-initiated moderation/activity events and site-side queued commands.

Keep the current Render service online until every check above passes. The current Neon quota
problem and the bot host's environment need to be resolved before calling the migration complete.
