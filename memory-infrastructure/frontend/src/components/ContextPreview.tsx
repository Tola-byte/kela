import type { RetrievedContext } from "../types/memory";

export default function ContextPreview({ context }: { context: RetrievedContext | null }) {
  if (!context) {
    return <p className="subtle">Run a query to see retrieved context.</p>;
  }

  return (
    <div className="context">
      <p className="subtle">Sources included: {context.sources_included}</p>
      <pre className="context__text">{context.context_text}</pre>
      {context.voice_summary && <p className="voice">{context.voice_summary}</p>}
    </div>
  );
}
