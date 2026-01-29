"use client";

import { Page } from "@/components/layout/Page";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/landing/Hero";
import { ExamplePreview } from "@/components/landing/ExamplePreview";
import { Features } from "@/components/landing/Features";
import { HowItWorks } from "@/components/landing/HowItWorks";

export default function Home() {
  return (
    <Page>
      <Navbar showTryCta />
      <main className="pb-10 md:pb-12">
        <Hero />
        <Features />
        <ExamplePreview />
        <HowItWorks />
      </main>
      <Footer />
    </Page>
  );
}
