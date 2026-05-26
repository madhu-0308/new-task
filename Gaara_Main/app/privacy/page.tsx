import Link from "next/link";

const SECTIONS = [
  {
    title: "1. What we collect",
    body: [
      "Account data: name, email, and authentication identifiers when you sign up via Firebase.",
      "Usage data: anonymous session statistics, form scores, and progress metrics tied to your account.",
      "Camera data: video frames are processed in real time for pose analysis. Frames are not stored or transmitted to our servers — only the extracted landmark coordinates are sent to our API for inference.",
      "Device data: browser type, OS, and approximate location (from IP) used for analytics and security.",
    ],
  },
  {
    title: "2. How we use your data",
    body: [
      "Provide the core coaching service: pose analysis, scoring, and progress tracking.",
      "Improve our AI models in aggregate. We do not train models on raw video data.",
      "Send service emails (account confirmations, important updates). We do not send marketing emails without consent.",
      "Comply with legal obligations.",
    ],
  },
  {
    title: "3. Camera and video data",
    body: [
      "All video processing happens in your browser. Raw video frames never leave your device.",
      "Only the numerical landmark coordinates (1,662 features per frame) are sent to our API for shot or pose recognition.",
      "We do not record, store, or share your camera feed under any circumstances.",
    ],
  },
  {
    title: "4. Sharing",
    body: [
      "We do not sell, rent, or share your personal data with third parties for marketing.",
      "We use trusted infrastructure providers (Firebase for auth, Vercel for hosting, AWS for inference) bound by their own privacy policies.",
      "We may disclose data if required by law or to protect rights and safety.",
    ],
  },
  {
    title: "5. Your rights",
    body: [
      "Access: request a copy of the data we hold about you.",
      "Deletion: request deletion of your account and associated data at any time.",
      "Correction: update inaccurate data through your account settings or by contacting us.",
      "Email admin@gaaraai.com to exercise any of these rights.",
    ],
  },
  {
    title: "6. Cookies",
    body: [
      "We use essential cookies for authentication and session management.",
      "Analytics cookies are anonymised and used only to improve product quality.",
      "You can disable cookies in your browser, though some features may not work.",
    ],
  },
  {
    title: "7. Data retention",
    body: [
      "Account data is retained as long as your account is active.",
      "Usage analytics are retained for up to 24 months in aggregate form.",
      "On account deletion, we remove personal data within 30 days.",
    ],
  },
  {
    title: "8. Children",
    body: [
      "Gaara AI is not directed at children under 13. We do not knowingly collect data from children under 13.",
      "If you believe a child has provided data without consent, contact us and we will delete it.",
    ],
  },
  {
    title: "9. Changes to this policy",
    body: [
      "We may update this policy from time to time. Material changes will be communicated via email or an in-app notice.",
      "Continued use of the service after changes constitutes acceptance of the updated policy.",
    ],
  },
  {
    title: "10. Contact",
    body: [
      "For privacy questions or requests, email admin@gaaraai.com.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-3xl mx-auto">
        <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
          Legal
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3">
          Privacy Policy
        </h1>
        <p className="text-sm text-[var(--color-muted)] mb-10 md:mb-14">
          Last updated: November 2025
        </p>

        <p className="text-base text-[var(--color-muted)] leading-relaxed mb-10 md:mb-14">
          Gaara AI (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) respects your privacy. This policy explains what data we
          collect, how we use it, and your rights. By using our services you agree to this policy.
        </p>

        <div className="space-y-10 md:space-y-12">
          {SECTIONS.map((s) => (
            <section key={s.title}>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight mb-4">{s.title}</h2>
              <ul className="space-y-2.5">
                {s.body.map((p, i) => (
                  <li key={i} className="text-sm md:text-base text-[var(--color-muted)] leading-relaxed pl-4 relative">
                    <span className="absolute left-0 top-2.5 w-1 h-1 rounded-full bg-[var(--color-dim)]" />
                    {p}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <div className="mt-16 pt-8 border-t border-[var(--color-bd)] flex flex-col sm:flex-row gap-4 justify-between text-sm">
          <Link href="/terms" className="text-[var(--color-muted)] hover:text-white">
            ← Terms of Service
          </Link>
          <Link href="/contact" className="text-[var(--color-muted)] hover:text-white">
            Contact us →
          </Link>
        </div>
      </div>
    </div>
  );
}
