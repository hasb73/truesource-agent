"use client";

import { CopilotSidebar } from "@copilotkit/react-core/v2";

export function CopilotAssistant({
  runtimeUrl,
  agentId,
}: {
  runtimeUrl: string | null;
  agentId: string;
}) {
  if (!runtimeUrl) {
    return (
      <section className="copilot-hint">
        CopilotKit is wired into the app shell and can be enabled by setting
        `NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL` and `NEXT_PUBLIC_COPILOTKIT_AGENT_ID`.
        The dashboard remains usable without the runtime.
      </section>
    );
  }

  return (
    <CopilotSidebar
      agentId={agentId}
      defaultOpen={false}
      labels={{
        modalHeaderTitle: "TrueSource Guardian",
        welcomeMessageText: "Ask for evidence, review drift, and inspect trusted knowledge.",
      }}
    />
  );
}
