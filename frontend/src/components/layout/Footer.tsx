import Link from "next/link";
import { Container } from "./Container";

export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] py-8">
      <Container>
        <p className="mb-4 text-center text-xs text-[var(--muted)]">
          Not affiliated with GitHub.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-[var(--muted)]">
          <Link
            href="#"
            className="rounded transition-colors hover:text-[var(--link)] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            Privacy
          </Link>
          <Link
            href="#"
            className="rounded transition-colors hover:text-[var(--link)] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            Terms
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded transition-colors hover:text-[var(--link)] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            GitHub
          </a>
        </div>
      </Container>
    </footer>
  );
}
