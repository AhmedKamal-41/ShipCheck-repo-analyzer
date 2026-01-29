interface SectionHeaderProps {
  title: string;
  subtitle?: string;
}

export function SectionHeader({ title, subtitle }: SectionHeaderProps) {
  return (
    <header className="mb-6 lg:mb-8">
      <h2 className="font-heading text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-1 text-sm text-slate-600 leading-relaxed">
          {subtitle}
        </p>
      )}
    </header>
  );
}
