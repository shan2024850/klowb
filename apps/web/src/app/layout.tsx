import type { ReactNode } from "react";
import { Workspace } from "../components/shell/workspace";
import "./styles.css";
export const metadata = { title: "klowb | Research workspace", description: "Research system health and feed provenance." };
export default function Layout({ children }: { children: ReactNode }) {
  return <html lang="en"><body><Workspace>{children}</Workspace></body></html>;
}
