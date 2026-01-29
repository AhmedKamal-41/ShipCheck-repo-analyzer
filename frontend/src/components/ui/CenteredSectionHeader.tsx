interface CenteredSectionHeaderProps {
  title: string;
  subtitle?: string;
}

export function CenteredSectionHeader({ title, subtitle }: CenteredSectionHeaderProps) {
  return (
    <header className="mx-auto max-w-2xl text-center mb-10">
      <h2 className="font-heading text-3xl font-semibold tracking-tight text-[var(--text)] mb-3 sm:text-4xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-0 text-base text-[var(--muted)] leading-relaxed">
          {subtitle}
        </p>
      )}
    </header>
  );
}
