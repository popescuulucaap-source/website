import { Container } from "@cloudflare/containers";
import { env as workerEnv } from "cloudflare:workers";

const APP_ENV_KEYS = [
  "ADMIN_DISCORD_USER_IDS",
  "ADMIN_PASSWORD",
  "DATABASE_URL",
  "DISCORD_BOT_TOKEN",
  "DISCORD_CLIENT_ID",
  "DISCORD_CLIENT_SECRET",
  "DISCORD_REDIRECT_URI",
  "DISCORD_TOKEN",
  "GARGAND_BOT_TOKEN",
  "GARGAND_BRIDGE_SECRET",
  "GARGAND_WEBSITE_URL",
  "GARGAND_YOUTUBE_CHANNEL_ID",
  "INVITE_URL",
  "NIGHTFALL_BRIDGE_SECRET",
  "NIGHTFALL_WEBSITE_URL",
  "NIGHTFALL_YOUTUBE_CHANNEL_ID",
  "OPENROUTER_API_KEY",
  "OPENROUTER_TEXT_MODEL",
  "PORT",
  "PYTHONUNBUFFERED",
  "ROBLOX_BRIDGE_SECRET",
  "ROBLOX_OAUTH_CLIENT_ID",
  "ROBLOX_OAUTH_CLIENT_SECRET",
  "ROBLOX_OAUTH_REDIRECT_URI",
  "SESSION_SECRET"
];

const containerEnvironment = Object.fromEntries(
  APP_ENV_KEYS
    .map((key) => [key, workerEnv[key]])
    .filter(([, value]) => typeof value === "string" && value.length > 0)
);

export class GargandContainer extends Container {
  defaultPort = 10000;
  // This keeps the site responsive between visits without running an idle
  // container indefinitely. Cloudflare may cold-start it after inactivity.
  sleepAfter = "10m";
  pingEndpoint = "localhost/health";
  envVars = containerEnvironment;
}

export default {
  async fetch(request, env) {
    const container = env.GARGAND.getByName("gargand-production");
    try {
      return await container.fetch(request);
    } catch (error) {
      console.error("Gargand container request failed:", error);
      return new Response(
        "Gargand is starting or temporarily unavailable. Please retry in a moment.",
        {
          status: 503,
          headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "no-store",
            "Retry-After": "5"
          }
        }
      );
    }
  }
};
