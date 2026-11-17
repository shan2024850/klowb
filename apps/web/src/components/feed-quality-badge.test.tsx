import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import type { FeedQuality } from "@klowb/types";
import { zFeedQuality } from "@klowb/types/validators";
import { FeedQualityBadge } from "./feed-quality-badge";

test("P1-WEB-004 each feed class has distinct visible provenance", () => {
  const expected: Record<FeedQuality,string> = {
    REALTIME_CONSOLIDATED: "Real-time · consolidated", REALTIME_EXCHANGE: "Real-time · exchange",
    REALTIME_SINGLE_VENUE: "Real-time · single venue", DELAYED: "Delayed", EOD: "End of day",
    UNOFFICIAL: "Unofficial", SIMULATED: "Simulated",
  };
  for (const quality of zFeedQuality.options) {
    const view = render(<FeedQualityBadge quality={quality}/>);
    expect(view.container.textContent).toBe(expected[quality]);
    view.unmount();
  }
});
