import type { IndicatorsResponse } from "@/lib/types";
import {
  buildMomentumAnalysis,
  buildSummary,
  buildTrendAnalysis,
  buildVolatilityAnalysis,
  type AnalysisSection,
  type Bias,
} from "@/lib/analysis";

interface AnalysisPanelProps {
  data: IndicatorsResponse;
}

function biasBadgeClasses(bias: Bias): string {
  switch (bias) {
    case "Bullish":
      return "bg-bull/15 text-bull border-bull/30";
    case "Bearish":
      return "bg-bear/15 text-bear border-bear/30";
    case "Mixed":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    default:
      return "bg-neutral-500/15 text-neutral-400 border-neutral-500/30";
  }
}

function Section({ section }: { section: AnalysisSection }) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-neutral-400">{section.label}</p>
        <span className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${biasBadgeClasses(section.bias)}`}>
          {section.bias}
        </span>
      </div>
      <ul className="mt-2 space-y-1">
        {section.reasons.length === 0 && (
          <li className="text-[11px] text-neutral-600">Belum ada data cukup.</li>
        )}
        {section.reasons.map((reason, idx) => (
          <li key={idx} className="text-[11px] leading-snug text-neutral-500">
            &bull; {reason}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AnalysisPanel({ data }: AnalysisPanelProps) {
  const trend = buildTrendAnalysis(data);
  const momentum = buildMomentumAnalysis(data);
  const volatility = buildVolatilityAnalysis(data);
  const summary = buildSummary(data);

  return (
    <section>
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        Market Analysis
      </h2>
      <div className="grid gap-2 sm:grid-cols-3">
        <Section section={trend} />
        <Section section={momentum} />
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-neutral-400">{volatility.label}</p>
            <span className="rounded border border-sky-500/30 bg-sky-500/15 px-1.5 py-0.5 text-[10px] font-medium text-sky-400">
              {volatility.state}
            </span>
          </div>
          <ul className="mt-2 space-y-1">
            {volatility.reasons.length === 0 && (
              <li className="text-[11px] text-neutral-600">Belum ada data cukup.</li>
            )}
            {volatility.reasons.map((reason, idx) => (
              <li key={idx} className="text-[11px] leading-snug text-neutral-500">
                &bull; {reason}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-2 rounded-lg border border-neutral-800 bg-neutral-900/60 p-3">
        <p className="text-xs leading-relaxed text-neutral-400">{summary}</p>
        <p className="mt-1.5 text-[10px] text-neutral-600">
          Ringkasan teknikal otomatis, bukan sinyal trading atau saran finansial.
        </p>
      </div>
    </section>
  );
}
