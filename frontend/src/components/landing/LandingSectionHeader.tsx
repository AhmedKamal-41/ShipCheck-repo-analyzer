type Align = "left" | "center";

interface LandingSectionHeaderProps {
  eyebrow: string;
  title: string;
  subtitle?: string;
  align?: Align;
  className?: string;
}

/**
 * Standardized landing-section header: eyebrow + h2 + optional subtitle.
 * Heading is locked to 40-44px Geist Sans 600 with -0.02em tracking
 * (via .font-heading) for visual consistency across the page.
 */
export function LandingSectionHeader({
  eyebrow,
  title,
  subtitle,
  align = "left",
  className = "",
}: LandingSectionHeaderProps) {
  const alignClass =
    align === "center"
      ? "mx-auto max-w-3xl text-center"
      : "max-w-2xl text-left";
  return (
    <header className={`${alignClass} ${className}`}>
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="font-heading mt-3 text-[2.5rem] font-semibold leading-[1.05] tracking-tight text-[var(--text)] sm:text-[2.75rem]">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-base leading-relaxed text-[var(--muted)]">
          {subtitle}
        </p>
      )}
    </header>
  );
}
