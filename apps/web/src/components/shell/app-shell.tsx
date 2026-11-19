import type { ReactNode } from "react";
import Link from "next/link";
import type { TradingMode } from "@klowb/types";
import { sections } from "../../lib/sections";

export function AppShell({ mode, children }: { mode?: TradingMode; children: ReactNode }) {
  return <>
    <a className="skip" href="#main">Skip to main content</a>
    <header><Link className="brand" href="/">klowb<span>.</span></Link>
      <span className="mode">Trading mode <strong>{mode?.toUpperCase() ?? "UNKNOWN"}</strong></span>
    </header>
    <div className="workspace">
      <nav aria-label="Workspace"><Link href="/">Command center</Link><Link href="/system">System health</Link>
        <hr/>{sections.map(([title, slug]) => <Link key={slug} href={"/" + slug}>{title}</Link>)}
      </nav>
      <main id="main" tabIndex={-1}>{children}</main>
    </div>
  </>;
}
