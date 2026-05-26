import Link from "next/link";
import { Check } from "lucide-react";

const TIERS = [
  {
    name: "Starter",
    price: "$0",
    period: "free forever",
    desc: "For individuals exploring AI coaching at home.",
    features: [
      "1 product (Yoga or Cricket)",
      "Basic form scoring",
      "Session history",
      "Community support",
    ],
    cta: "Start free",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "per month",
    desc: "Full access for serious athletes and students.",
    features: [
      "All products included",
      "Detailed criteria breakdown",
      "Voice coaching",
      "Progress analytics",
      "Email support",
    ],
    cta: "Start Pro trial",
    highlight: true,
  },
  {
    name: "Studio",
    price: "Custom",
    period: "contact us",
    desc: "For studios, academies, and white-label clients.",
    features: [
      "Everything in Pro",
      "Custom branding",
      "Multi-user dashboard",
      "Custom AI models",
      "Dedicated support",
    ],
    cta: "Talk to sales",
    highlight: false,
  },
];

export default function PricingPage() {
  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 md:mb-16">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
            Pricing
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-5">
            Simple, transparent pricing.
          </h1>
          <p className="text-base md:text-lg text-[var(--color-muted)] max-w-xl mx-auto leading-relaxed">
            Start free, upgrade when you&apos;re ready. Custom plans for studios and clients.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
          {TIERS.map((t) => (
            <div
              key={t.name}
              className={`flex flex-col rounded-lg p-6 md:p-8 border transition-colors ${
                t.highlight
                  ? "bg-[var(--color-bg-3)] border-[var(--color-yoga)]"
                  : "bg-[var(--color-bg-2)] border-[var(--color-bd)]"
              }`}
            >
              {t.highlight && (
                <div className="text-[10px] font-bold tracking-[2px] uppercase text-[var(--color-yoga)] mb-3">
                  Most Popular
                </div>
              )}
              <h3 className="text-xl font-bold mb-2">{t.name}</h3>
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-3xl md:text-4xl font-extrabold tracking-tight">{t.price}</span>
              </div>
              <div className="text-xs text-[var(--color-muted)] mb-4">{t.period}</div>
              <p className="text-sm text-[var(--color-muted)] leading-relaxed mb-6">{t.desc}</p>
              <ul className="space-y-3 mb-8 flex-1">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <Check size={16} className="text-[var(--color-cricket)] mt-0.5 flex-shrink-0" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={t.name === "Studio" ? "/contact" : "/login"}
                className={`block text-center py-3 rounded text-sm font-bold transition-opacity ${
                  t.highlight
                    ? "bg-white text-[var(--color-bg)] hover:opacity-90"
                    : "border border-[var(--color-bd-2)] text-white hover:bg-[var(--color-bg-3)]"
                }`}
              >
                {t.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
