import Link from "next/link";
import { Container } from "./Container";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 py-10">
      <Container>
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
          <Link href="#" className="hover:text-slate-900">
            Privacy
          </Link>
          <Link href="#" className="hover:text-slate-900">
            Terms
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-900"
          >
            GitHub
          </a>
        </div>
      </Container>
    </footer>
  );
}
