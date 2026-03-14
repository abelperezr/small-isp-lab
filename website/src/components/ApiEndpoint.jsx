const METHOD_TINT = {
  GET: "rgba(34,197,94,0.22)",
  POST: "rgba(59,130,246,0.22)",
  PUT: "rgba(245,158,11,0.22)",
  PATCH: "rgba(236,72,153,0.22)",
  DELETE: "rgba(239,68,68,0.22)",
};

export default function ApiEndpoint({
  method = "GET",
  path,
  summary,
  auth = "Required",
  request = "",
  response = "",
}) {
  const methodUpper = method.toUpperCase();

  return (
    <section className="api-endpoint">
      <div className="api-endpoint__head">
        <span
          className="api-endpoint__method"
          style={{ background: METHOD_TINT[methodUpper] || METHOD_TINT.GET }}
        >
          {methodUpper}
        </span>
        <code className="api-endpoint__path">{path}</code>
      </div>

      {summary ? <p>{summary}</p> : null}
      <p>
        <strong>Auth:</strong> {auth}
      </p>

      {request ? (
        <>
          <h4>Request</h4>
          <pre className="prism-code language-json">
            <code>{request}</code>
          </pre>
        </>
      ) : null}

      {response ? (
        <>
          <h4>Response</h4>
          <pre className="prism-code language-json">
            <code>{response}</code>
          </pre>
        </>
      ) : null}
    </section>
  );
}
