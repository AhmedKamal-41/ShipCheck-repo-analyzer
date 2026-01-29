"use client";

import { Tabs } from "@/components/ui/Tabs";

export const REPORT_TABS = [
  { id: "overview", label: "Overview" },
  { id: "checks", label: "Checks" },
  { id: "security", label: "Security" },
  { id: "cicd", label: "CI/CD" },
  { id: "interview-pack", label: "Interview Pack" },
] as const;

export type ReportTabId = (typeof REPORT_TABS)[number]["id"];

interface ReportTabsProps {
  activeId: ReportTabId;
  onChange: (id: ReportTabId) => void;
}

export function ReportTabs({ activeId, onChange }: ReportTabsProps) {
  return (
    <Tabs
      tabs={REPORT_TABS.map((t) => ({ id: t.id, label: t.label }))}
      activeId={activeId}
      onChange={(id) => onChange(id as ReportTabId)}
    />
  );
}
