"use client";

type Actor = {
  id: string;
  name: string;
  role: string;
  tenant_id: string;
};

export function AuthControls({
  actor,
}: {
  actor: Actor | null;
}) {
  if (!actor) {
    return <div className="auth-badge">Dev auth · reviewer access simulated</div>;
  }

  return (
    <div className="auth-controls">
      <div className="auth-user">
        <strong>{actor.name}</strong>
        <span>{actor.role}</span>
      </div>
      <div className="auth-badge">Development mode</div>
    </div>
  );
}
