"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { useSystemInfo } from "../../lib/api";
import { AppShell } from "./app-shell";

function ConnectedShell({ children }: { children: ReactNode }) {
  const info = useSystemInfo();
  return <AppShell mode={info.isError ? undefined : info.data?.trading_mode}>{children}</AppShell>;
}
export function Workspace({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: {
    retry: false, refetchInterval: 30000, staleTime: 5000,
  } } }));
  return <QueryClientProvider client={client}><ConnectedShell>{children}</ConnectedShell></QueryClientProvider>;
}
