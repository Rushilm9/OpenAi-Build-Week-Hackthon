import { AlertTriangle, ExternalLink } from "lucide-react";
import type { EvidenceItem } from "../../types";

interface EvidencePanelProps {
  title: string;
  items: EvidenceItem[];
  emptyMessage: string;
}

function formatAsOf(value?: string | null) {
  if (!value) return "Time not reported";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

export function EvidencePanel({ title, items, emptyMessage }: EvidencePanelProps) {
  return (
    <section className="space-y-2" aria-label={title}>
      <h4 className="text-xs font-black uppercase tracking-wider text-primary">{title}</h4>
      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border bg-neutral-50 p-3 text-xs text-muted">
          {emptyMessage}
        </p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          {items.map((item, index) => (
            <article
              key={`${item.source}-${item.as_of || "unknown"}-${index}`}
              className="rounded-lg border border-border bg-white p-3 text-xs"
            >
              <div className="flex flex-wrap items-center gap-1.5">
                {item.url ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-bold text-accent-dark hover:underline"
                  >
                    {item.source}
                    <ExternalLink size={11} aria-hidden="true" />
                  </a>
                ) : (
                  <span className="font-bold text-primary">{item.source}</span>
                )}
                <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-muted">
                  {item.status}
                </span>
                <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-muted">
                  {item.freshness}
                </span>
                <span className="rounded border border-border bg-neutral-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-muted">
                  {item.stance}
                </span>
              </div>
              <p className="mt-2 leading-relaxed text-primary">{item.summary}</p>
              <p className="mt-2 font-mono text-[10px] text-muted">As of {formatAsOf(item.as_of)}</p>
              {item.warning && (
                <p className="mt-2 flex items-start gap-1 text-[10px] font-semibold text-amber-700">
                  <AlertTriangle size={11} className="mt-0.5 shrink-0" aria-hidden="true" />
                  {item.warning}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
