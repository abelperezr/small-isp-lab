export default function TechBadge({ label, tone = "success" }) {
  const dotColor =
    tone === "warning"
      ? "#f59e0b"
      : tone === "danger"
        ? "#ef4444"
        : tone === "info"
          ? "#3b82f6"
          : "#22c55e";

  return (
    <span className="tech-badge">
      <span className="tech-badge__dot" style={{ background: dotColor }} aria-hidden="true" />
      {label}
    </span>
  );
}
