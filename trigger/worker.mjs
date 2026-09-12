const api = process.env.TRUESOURCE_API_URL ?? "http://backend:8000";
const intervalMs = Number(process.env.TRIGGER_SCAN_INTERVAL_MS ?? "900000");
const enabled = String(process.env.WORKER_ENABLED ?? "false").toLowerCase() === "true";

async function runScan() {
  try {
    const response = await fetch(`${api}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: ["Payments"], trigger: "worker" }),
    });
    const payload = await response.json();
    console.log(`[worker] queued scan ${payload.scan_id ?? "unknown"}`);
  } catch (error) {
    console.error("[worker] scan request failed", error);
  }
}

console.log(`[worker] ready; target=${api}; enabled=${enabled}; intervalMs=${intervalMs}`);

if (enabled) {
  void runScan();
  setInterval(() => {
    void runScan();
  }, intervalMs);
} else {
  setInterval(() => {
    console.log("[worker] idle heartbeat");
  }, Math.min(intervalMs, 60000));
}
