import Link from "next/link";

const SECTIONS = [
  {
    title: "1. Acceptance",
    body: [
      "By accessing or using Gaara AI services (the \"Services\"), you agree to be bound by these Terms.",
      "If you do not agree, please do not use our Services.",
    ],
  },
  {
    title: "2. Service description",
    body: [
      "Gaara AI provides AI-powered pose analysis and coaching feedback for sports and wellness practice via web applications.",
      "Specific features may change over time as we improve and expand our products.",
    ],
  },
  {
    title: "3. Accounts",
    body: [
      "You must provide accurate information when creating an account.",
      "You are responsible for maintaining the security of your credentials.",
      "You must be at least 13 years old (or the legal age in your jurisdiction) to use the Services.",
    ],
  },
  {
    title: "4. Acceptable use",
    body: [
      "Do not attempt to reverse-engineer, decompile, or scrape the Services.",
      "Do not use the Services to harass, abuse, or harm others.",
      "Do not interfere with the Services' security or operation.",
      "Do not redistribute, resell, or sublicense the Services without written permission.",
    ],
  },
  {
    title: "5. Health and safety disclaimer",
    body: [
      "Gaara AI provides feedback based on computer-vision analysis. It is NOT a substitute for professional medical, fitness, or sports coaching advice.",
      "Consult a qualified medical professional before beginning any new exercise programme.",
      "Stop immediately if you experience pain, dizziness, or discomfort. You use the Services at your own risk.",
      "We are not liable for any injury or harm resulting from use of the Services.",
    ],
  },
  {
    title: "6. Camera and content",
    body: [
      "Video frames are processed locally in your browser and are not transmitted or stored. Only landmark coordinates are sent for inference.",
      "Form scores, session history, and progress data tied to your account are stored to provide the Service.",
      "You retain ownership of any data you generate. We retain rights to aggregate, anonymised usage statistics.",
    ],
  },
  {
    title: "7. Subscriptions and payment",
    body: [
      "Free tier features are available without payment.",
      "Paid plans are billed in advance on a monthly or annual basis.",
      "Refunds are issued at our discretion, typically pro-rated for unused time.",
      "We may change pricing with 30 days' notice.",
    ],
  },
  {
    title: "8. Intellectual property",
    body: [
      "All software, models, designs, and content on the Services are owned by Gaara AI or our licensors.",
      "These Terms grant you a limited, non-exclusive, non-transferable licence to use the Services for personal or business use.",
    ],
  },
  {
    title: "9. Termination",
    body: [
      "You may delete your account at any time.",
      "We may suspend or terminate accounts that violate these Terms.",
      "On termination, your right to use the Services ends immediately.",
    ],
  },
  {
    title: "10. Disclaimers",
    body: [
      "The Services are provided \"as is\" without warranty of any kind.",
      "We do not guarantee uninterrupted operation, error-free results, or perfect form-scoring accuracy.",
    ],
  },
  {
    title: "11. Limitation of liability",
    body: [
      "To the maximum extent permitted by law, Gaara AI is not liable for indirect, incidental, or consequential damages.",
      "Our total liability for any claim is limited to the amount you paid us in the 12 months preceding the claim.",
    ],
  },
  {
    title: "12. Changes to these Terms",
    body: [
      "We may update these Terms from time to time. Material changes will be communicated via email or an in-app notice.",
      "Continued use after changes constitutes acceptance of the updated Terms.",
    ],
  },
  {
    title: "13. Governing law",
    body: [
      "These Terms are governed by the laws of India. Disputes shall be resolved in the courts of Chennai, India.",
    ],
  },
  {
    title: "14. Contact",
    body: [
      "Questions about these Terms? Email admin@gaaraai.com.",
    ],
  },
];

export default function TermsPage() {
  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-3xl mx-auto">
        <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
          Legal
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3">
          Terms of Service
        </h1>
        <p className="text-sm text-[var(--color-muted)] mb-10 md:mb-14">
          Last updated: November 2025
        </p>

        <p className="text-base text-[var(--color-muted)] leading-relaxed mb-10 md:mb-14">
          These Terms of Service govern your use of Gaara AI. Read them carefully — they include a
          health and safety disclaimer specific to AI coaching products.
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
          <Link href="/privacy" className="text-[var(--color-muted)] hover:text-white">
            ← Privacy Policy
          </Link>
          <Link href="/contact" className="text-[var(--color-muted)] hover:text-white">
            Contact us →
          </Link>
        </div>
      </div>
    </div>
  );
}
