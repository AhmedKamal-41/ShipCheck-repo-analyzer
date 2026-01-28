interface CenteredSectionHeaderProps {
  title: string;
  subtitle?: string;
}

export function CenteredSectionHeader({ title, subtitle }: CenteredSectionHeaderProps) {
  return (
    <header className="mx-auto max-w-2xl text-center mb-10 lg:mb-12">
      <h2 className="font-heading text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-3 text-base text-slate-600 leading-relaxed sm:text-lg">
          {subtitle}
        </p>
      )}
    </header>
  );
}
