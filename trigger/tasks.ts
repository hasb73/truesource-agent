import { schedules } from "@trigger.dev/sdk";

export const documentationDriftScan = schedules.task({
  id: "documentation-drift-scan",
  cron: {
    pattern: "*/15 * * * *",
    timezone: "UTC"
  },
  run: async () => {
    const api = process.env.TRUESOURCE_API_URL ?? "http://localhost:8000";
    const response = await fetch(`${api}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: ["Payments"], trigger: "schedule" })
    });
    if (!response.ok) throw new Error(`TrueSource scan failed: ${response.status}`);
    return response.json();
  }
});
