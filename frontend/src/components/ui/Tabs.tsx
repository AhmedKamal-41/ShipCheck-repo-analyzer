"use client";

export type TabItem = { id: string; label: string };

interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeId, onChange, className = "" }: TabsProps) {
  return (
    <div
      className={`border-b border-[#d0d7de] bg-white ${className}`}
      role="tablist"
    >
      <div className="flex gap-1">
        {tabs.map((tab) => {
          const isActive = tab.id === activeId;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.id)}
              className={`relative -mb-px rounded-t border border-transparent px-4 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? "border-b-0 border-[#d0d7de] border-t border-x bg-white text-[#1f2328]"
                  : "border-b-transparent text-[#57606a] hover:text-[#1f2328]"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
