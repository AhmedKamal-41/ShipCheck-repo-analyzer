interface SectionHeaderProps {
  title: string;
  subtitle?: string;
}

export function SectionHeader({ title, subtitle }: SectionHeaderProps) {
  return (
    <header className="mb-8 lg:mb-10">
      <h2 className="font-heading text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-1 text-base text-slate-600 sm:text-lg leading-relaxed">
          {subtitle}
        </p>
      )}
    </header>
  );
}
