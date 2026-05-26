import Link from "next/link";
import { ArrowRight } from "lucide-react";

const PRODUCTS = [
  {
    href: "/products/yoga",
    badge: "Yoga · AI Coaching",
    badgeColor: "var(--color-yoga)",
    title: "Yoga AI Coach",
    description:
      "Real-time pose correction for Hatha Yoga and wellness programmes. The AI identifies misalignments across 5 key criteria per pose.",
    stats: [
      { n: "10+", l: "Poses" },
      { n: "5", l: "Form Checks" },
      { n: "Live", l: "Corrections" },
    ],
  },
  {
    href: "/products/cricket",
    badge: "Cricket · Batting Coach",
    badgeColor: "var(--color-cricket)",
    title: "Cricket AI Coach",
    description:
      "Shot-specific coaching for the cover drive and pull shot. LSTM-powered recognition delivers step-by-step refinement cues as you bat.",
    stats: [
      { n: "2", l: "Shots" },
      { n: "5", l: "Form Checks" },
      { n: "30fps", l: "Real-Time" },
    ],
  },
];

export default function ProductsPage() {
  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-6xl mx-auto">
        <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
          Products
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-5">
          AI coaching products,
          <br className="hidden md:block" /> built to ship.
        </h1>
        <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-12 md:mb-16 max-w-2xl">
          Two flagship platforms. Both available to license, customise, or white-label for your brand.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 md:gap-6">
          {PRODUCTS.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              className="block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-8 hover:bg-[var(--color-bg-3)] hover:border-[var(--color-bd-2)] transition-colors group"
            >
              <div
                className="text-[10px] font-bold tracking-[2px] uppercase mb-4"
                style={{ color: p.badgeColor }}
              >
                {p.badge}
              </div>
              <h3 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-3">
                {p.title}
              </h3>
              <p className="text-sm md:text-base text-[var(--color-muted)] leading-relaxed mb-6">
                {p.description}
              </p>
              <div className="flex gap-6 md:gap-8 py-5 border-t border-[var(--color-bd)] mb-5">
                {p.stats.map((s) => (
                  <div key={s.l}>
                    <div className="text-xl md:text-2xl font-extrabold" style={{ color: p.badgeColor }}>
                      {s.n}
                    </div>
                    <div className="text-xs text-[var(--color-muted)] mt-1">{s.l}</div>
                  </div>
                ))}
              </div>
              <span className="inline-flex items-center gap-2 text-sm font-bold group-hover:gap-3 transition-all">
                Learn more <ArrowRight size={16} />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
