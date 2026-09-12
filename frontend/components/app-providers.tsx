"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";

const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL;
const agentId = process.env.NEXT_PUBLIC_COPILOTKIT_AGENT_ID || "truesource_guardian";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return runtimeUrl ? (
    <CopilotKit runtimeUrl={runtimeUrl} agent={agentId} showDevConsole={false}>
      {children}
    </CopilotKit>
  ) : (
    children
  );
}
