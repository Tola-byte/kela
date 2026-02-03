import type { MemoryEntry } from "../types/memory";

export default function MemoryTimeline({ entries }: { entries: MemoryEntry[] }) {
  if (!entries.length) {
    return <p className="subtle">No memory entries yet.</p>;
  }

  return (
    <div className="timeline">
      {entries.map((entry) => (
        <div className="timeline__item" key={entry.id}>
          <div>
            <p className="eyebrow">{entry.content_type}</p>
            <h3>{entry.title}</h3>
            <p className="subtle">{entry.content_preview}</p>
          </div>
          <div className="timeline__meta">
            <span>Decay {entry.relevance_decay.toFixed(2)}</span>
            <span>Access {entry.access_count}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
