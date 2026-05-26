"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown } from "lucide-react";

const FAQS = [
  {
    cat: "Getting Started",
    items: [
      {
        q: "What do I need to use Gaara AI?",
        a: "Just a webcam-equipped device (laptop, phone, or tablet) and a modern browser. There's nothing to install — everything runs in the browser.",
      },
      {
        q: "Do I need a special webcam or sensor?",
        a: "No. A standard 720p webcam at 30fps is enough. Better lighting and a clear background give better results, but no specialist hardware is needed.",
      },
      {
        q: "How much space do I need?",
        a: "About 2m × 2m for yoga, slightly more for cricket batting practice. Make sure your full body is visible to the camera.",
      },
    ],
  },
  {
    cat: "Privacy & Data",
    items: [
      {
        q: "Are my video frames stored or transmitted?",
        a: "No. All video processing happens in your browser. Only the extracted landmark coordinates (numerical data, no images) are sent to our API for shot or pose recognition.",
      },
      {
        q: "Can I delete my account and data?",
        a: "Yes. Email admin@gaaraai.com and we'll remove your account and all personal data within 30 days.",
      },
      {
        q: "Do you train AI models on my data?",
        a: "We do not train models on raw video. Aggregate, anonymised usage statistics may be used to improve product quality.",
      },
    ],
  },
  {
    cat: "Pricing & Plans",
    items: [
      {
        q: "Is there a free plan?",
        a: "Yes. Starter is free forever and includes one product (Yoga or Cricket) with basic form scoring and session history.",
      },
      {
        q: "What does Pro include?",
        a: "Full access to all products, detailed criteria breakdown, voice coaching, progress analytics, and email support — for $19/month.",
      },
      {
        q: "Can I cancel anytime?",
        a: "Yes. Cancel from your account settings. You'll retain access until the end of the current billing period.",
      },
    ],
  },
  {
    cat: "AI & Accuracy",
    items: [
      {
        q: "How accurate is the form scoring?",
        a: "Our LSTM models are trained on professionally annotated data and achieve >90% accuracy on the criteria they evaluate. Scoring is calibrated against certified coaches.",
      },
      {
        q: "Will it work for my body type?",
        a: "Yes. Gaara AI uses biomechanical relationships (angles, ratios, alignments) rather than absolute positions — so it works across body types, heights, and proportions.",
      },
      {
        q: "Can I use it left-handed?",
        a: "Yes. The cricket app supports both left- and right-hand batting. Yoga poses are symmetric or analysed on both sides.",
      },
    ],
  },
  {
    cat: "Business & Licensing",
    items: [
      {
        q: "Can I license Gaara AI for my studio or academy?",
        a: "Yes. Our Studio plan offers custom branding, multi-user dashboards, and dedicated support. Contact us at admin@gaaraai.com for a quote.",
      },
      {
        q: "Can you build a custom AI coaching product for my sport?",
        a: "Yes. We license our pose-recognition pipeline for new sports and wellness products. Reach out via the contact page with your use case.",
      },
      {
        q: "Do you offer a white-label version?",
        a: "Yes — under our Studio plan. Contact us to discuss branding, custom domains, and API access.",
      },
    ],
  },
];

export default function FAQPage() {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-3xl mx-auto">
        <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
          Help
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-5">
          Frequently asked questions.
        </h1>
        <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-12 md:mb-16">
          Quick answers to the most common questions. Don&apos;t see yours?{" "}
          <Link href="/contact" className="text-white underline hover:no-underline">
            Get in touch
          </Link>
          .
        </p>

        <div className="space-y-10 md:space-y-12">
          {FAQS.map((cat) => (
            <div key={cat.cat}>
              <h2 className="text-xs font-bold tracking-widest uppercase text-[var(--color-dim)] mb-4">
                {cat.cat}
              </h2>
              <div className="space-y-2">
                {cat.items.map((item) => {
                  const key = `${cat.cat}-${item.q}`;
                  const isOpen = open === key;
                  return (
                    <div
                      key={item.q}
                      className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => setOpen(isOpen ? null : key)}
                        className="w-full flex items-center justify-between gap-4 p-5 md:p-6 text-left hover:bg-[var(--color-bg-3)] transition-colors"
                      >
                        <span className="text-sm md:text-base font-semibold">{item.q}</span>
                        <ChevronDown
                          size={18}
                          className={`text-[var(--color-muted)] flex-shrink-0 transition-transform ${
                            isOpen ? "rotate-180" : ""
                          }`}
                        />
                      </button>
                      {isOpen && (
                        <div className="px-5 md:px-6 pb-5 md:pb-6 text-sm md:text-base text-[var(--color-muted)] leading-relaxed">
                          {item.a}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 md:mt-20 bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-8 text-center">
          <h3 className="text-xl md:text-2xl font-bold mb-2">Still have questions?</h3>
          <p className="text-sm text-[var(--color-muted)] mb-5">
            We read every email at admin@gaaraai.com and respond within one business day.
          </p>
          <Link
            href="/contact"
            className="inline-block px-6 py-3 bg-white text-[var(--color-bg)] font-bold rounded text-sm hover:opacity-90 transition-opacity"
          >
            Contact us
          </Link>
        </div>
      </div>
    </div>
  );
}
