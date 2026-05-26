import Link from "next/link";
import { ArrowRight, Rocket, Heart, Sparkles, GraduationCap, MapPin, Clock } from "lucide-react";

const VALUES = [
  {
    Icon: Rocket,
    title: "Move fast, ship often",
    body: "We prefer iterating in production over endless planning. Strong opinions, weakly held.",
  },
  {
    Icon: Heart,
    title: "Care about the craft",
    body: "Code quality, design polish, and user empathy are non-negotiable. We sweat the small stuff.",
  },
  {
    Icon: Sparkles,
    title: "Own your work",
    body: "Hire smart people and trust them. Every engineer ships features end-to-end with full context.",
  },
  {
    Icon: GraduationCap,
    title: "Learn continuously",
    body: "Books, courses, conferences, hackathons — your growth is part of the job, not a side activity.",
  },
];

const POSITIONS = [
  {
    title: "Senior ML Engineer",
    team: "AI / Computer Vision",
    location: "Chennai / Remote",
    type: "Full-time",
    desc: "Lead next-gen pose recognition models. Strong PyTorch / TensorFlow experience required.",
  },
  {
    title: "Full-Stack Engineer",
    team: "Product",
    location: "Chennai / Remote",
    type: "Full-time",
    desc: "Ship coaching products end-to-end. Next.js, React, FastAPI, and a designer's eye.",
  },
  {
    title: "Sports Biomechanics Researcher",
    team: "Research",
    location: "Chennai",
    type: "Full-time",
    desc: "Define the form-scoring criteria for new sports. Background in kinesiology or sports science.",
  },
  {
    title: "Founding Designer",
    team: "Design",
    location: "Remote",
    type: "Full-time",
    desc: "Own the visual language of every Gaara product. Figma fluency + interaction design taste.",
  },
];

export default function CareersPage() {
  return (
    <>
      {/* HERO */}
      <section className="relative pt-28 pb-12 md:pt-40 md:pb-20 px-5 md:px-12 overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_60%_at_50%_30%,rgba(167,139,250,0.10),transparent_60%)]" />
        <div className="max-w-4xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
            Career
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.05] mb-5">
            We&apos;re hiring.
          </h1>
          <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed max-w-2xl">
            We&apos;re a small team putting professional-grade coaching into every athlete&apos;s
            pocket. Join us if you care about computer vision, beautiful products, and helping
            people improve.
          </p>
        </div>
      </section>

      {/* VALUES */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-3">
            How we work
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-12">
            What you sign up for.
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5">
            {VALUES.map((v) => (
              <div
                key={v.title}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 hover:border-[var(--color-bd-2)] transition-colors"
              >
                <div className="w-11 h-11 rounded-lg bg-[var(--color-yoga)]/10 flex items-center justify-center mb-4">
                  <v.Icon className="text-[var(--color-yoga)]" size={22} />
                </div>
                <h3 className="text-base font-bold mb-2">{v.title}</h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed">{v.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* OPEN POSITIONS */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-10">
            <div>
              <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
                Open roles
              </div>
              <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
                {POSITIONS.length} open positions.
              </h2>
            </div>
            <Link
              href="/contact"
              className="text-sm font-semibold text-[var(--color-muted)] hover:text-white inline-flex items-center gap-1.5"
            >
              Don&apos;t see your role? Get in touch <ArrowRight size={14} />
            </Link>
          </div>

          <div className="space-y-3">
            {POSITIONS.map((p) => (
              <Link
                key={p.title}
                href="/contact"
                className="block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-5 md:p-6 hover:border-[var(--color-bd-2)] hover:bg-[var(--color-bg-3)] transition-colors group"
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <h3 className="text-lg md:text-xl font-bold">{p.title}</h3>
                      <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--color-cricket)] bg-[var(--color-cricket)]/10 px-2 py-0.5 rounded">
                        {p.team}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--color-muted)] leading-relaxed mb-3 md:mb-2">
                      {p.desc}
                    </p>
                    <div className="flex flex-wrap gap-4 text-xs text-[var(--color-muted)]">
                      <span className="inline-flex items-center gap-1.5">
                        <MapPin size={13} /> {p.location}
                      </span>
                      <span className="inline-flex items-center gap-1.5">
                        <Clock size={13} /> {p.type}
                      </span>
                    </div>
                  </div>
                  <ArrowRight
                    className="text-[var(--color-muted)] group-hover:text-white group-hover:translate-x-1 transition-all flex-shrink-0"
                    size={20}
                  />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-5 md:px-12 py-16 md:py-24 text-center bg-[var(--color-bg-1)] border-t border-[var(--color-bd)]">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
            Want to apply?
          </h2>
          <p className="text-base md:text-lg text-[var(--color-muted)] mb-8 max-w-xl mx-auto leading-relaxed">
            Send us your resume and a short note on what you want to build. We read every email.
          </p>
          <a
            href="mailto:admin@gaaraai.com?subject=Careers application"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-[var(--color-bg)] font-bold rounded text-sm hover:opacity-90 transition-opacity"
          >
            Email us your resume <ArrowRight size={16} />
          </a>
        </div>
      </section>
    </>
  );
}
