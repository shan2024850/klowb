"use client";
import { useSystemInfo } from "../lib/api";
import { FeedQualityBadge } from "./feed-quality-badge";

export function FeedLegend() {
  const info = useSystemInfo();
  return <section aria-labelledby="quality-title"><h2 id="quality-title">Feed quality</h2>
    {info.isError ? <p role="alert">Feed definitions unavailable.</p> : !info.data ? <p>Loading feed definitions…</p> :
      <dl>{info.data.feed_quality_legend.map(item => <div key={item.value}><dt><FeedQualityBadge quality={item.value}/></dt><dd>{item.description}</dd></div>)}</dl>}
  </section>;
}
