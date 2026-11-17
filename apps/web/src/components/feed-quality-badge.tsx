import type { FeedQuality } from "@klowb/types";

export const qualityLabels: Record<FeedQuality, string> = {
  REALTIME_CONSOLIDATED: "Real-time · consolidated",
  REALTIME_EXCHANGE: "Real-time · exchange",
  REALTIME_SINGLE_VENUE: "Real-time · single venue",
  DELAYED: "Delayed", EOD: "End of day", UNOFFICIAL: "Unofficial", SIMULATED: "Simulated",
};
export function FeedQualityBadge({ quality }: { quality: FeedQuality }) {
  return <span className="quality">{qualityLabels[quality]}</span>;
}
