import { useMemo, useState } from "react";

export default function CodeExample({ examples = [], hint = "" }) {
  const normalized = useMemo(
    () => examples.filter((item) => item && item.label && item.code),
    [examples],
  );
  const [active, setActive] = useState(0);

  if (!normalized.length) {
    return null;
  }

  const current = normalized[Math.min(active, normalized.length - 1)];

  return (
    <div className="code-example">
      <div className="code-example__tabs" role="tablist" aria-label="Code example tabs">
        {normalized.map((item, index) => (
          <button
            key={`${item.label}-${index}`}
            type="button"
            className={`code-example__tab ${index === active ? "is-active" : ""}`}
            onClick={() => setActive(index)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <pre className="prism-code language-bash">
        <code>{current.code}</code>
      </pre>

      {hint ? <p className="code-example__hint">{hint}</p> : null}
    </div>
  );
}
