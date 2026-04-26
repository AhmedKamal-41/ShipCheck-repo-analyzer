"use client";

import { Page } from "@/components/layout/Page";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { Problem } from "@/components/landing/Problem";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Audiences } from "@/components/landing/Audiences";
import { Faq } from "@/components/landing/Faq";
import { ExamplePreview } from "@/components/landing/ExamplePreview";
import { FinalCta } from "@/components/landing/FinalCta";

export default function Home() {
  return (
    <Page>
      <Navbar showTryCta />
      <main>
        <Hero />
        <Features />
        <Problem />
        <HowItWorks />
        <Audiences />
        <Faq />
        <ExamplePreview />
        <FinalCta />
      </main>
      <Footer />
    </Page>
  );
}
