import Link from "next/link";
import { ArrowRight, Activity, Scale, Wind, Anchor, GitBranch, Eye, Camera, Zap, BarChart3, Wrench } from "lucide-react";

const CRITERIA = [
  {
    Icon: Activity,
    title: "Hip Alignment",
    body: "Tracks pelvic tilt and rotation across standing and balance poses to prevent the most common source of misalignment.",
  },
  {
    Icon: Scale,
    title: "Weight Distribution",
    body: "Analyses balance across both feet to ensure stability and proper energetic foundation in every posture.",
  },
  {
    Icon: Wind,
    title: "Arm Extension",
    body: "Verifies full shoulder-width extension — collapsed arms reduce balance and weaken the pose's expression.",
  },
  {
    Icon: Anchor,
    title: "Knee Alignment",
    body: "Checks that the front knee tracks directly over the foot — preventing strain and instability in standing poses.",
  },
  {
    Icon: GitBranch,
    title: "Spinal Position",
    body: "Monitors spine length and rotation to maintain a neutral, lifted posture throughout each transition.",
  },
];

const POSES = [
  "Warrior I", "Warrior II", "Warrior III", "Tree Pose",
  "Triangle Pose", "Mountain Pose", "Downward Dog", "Half Moon",
  "Eagle Pose", "Chair Pose",
];

const STEPS = [
  {
    Icon: Camera,
    num: "01",
    title: "Open your camera",
    body: "Allow webcam access. The AI begins a brief warm-up phase to calibrate body landmarks.",
  },
  {
    Icon: Zap,
    num: "02",
    title: "Practise live",
    body: "Move into the pose. The AI tracks 33 landmarks in real time and flags misalignments instantly.",
  },
  {
    Icon: BarChart3,
    num: "03",
    title: "Track progress",
    body: "Every attempt scored out of 100. Your dashboard tracks streak, history, and improvement.",
  },
];

export default function YogaProductPage() {
  return (
    <>
      {/* HERO */}
      <section className="relative pt-28 pb-12 md:pt-40 md:pb-20 px-5 md:px-12 overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_60%_at_50%_30%,rgba(167,139,250,0.12),transparent_60%)]" />
        <div className="max-w-6xl mx-auto">
          <Link
            href="/products"
            className="text-xs text-[var(--color-muted)] hover:text-white inline-flex items-center gap-1.5 mb-6"
          >
            ← All products
          </Link>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 text-[10px] md:text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-5">
                <span className="w-6 h-px bg-[var(--color-yoga)]" />
                Yoga · AI Coaching
              </div>
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.05] mb-5">
                Yoga form,
                <br />
                <span className="text-[var(--color-yoga)]">corrected in real time.</span>
              </h1>
              <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-8 max-w-xl">
                The Yoga AI Coach analyses your posture across 5 biomechanical criteria — providing
                instant cues that previously required a one-on-one instructor.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-2 mb-4 bg-[var(--color-yoga)]/10 border border-[var(--color-yoga)]/30 rounded text-xs font-bold tracking-widest uppercase text-[var(--color-yoga)] w-fit">
                <Wrench size={14} /> Still building…
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  disabled
                  className="px-6 py-3.5 bg-[var(--color-yoga)]/50 text-[var(--color-bg)] font-bold rounded text-sm flex items-center justify-center gap-2 cursor-not-allowed opacity-70"
                >
                  Still Building… <Wrench size={16} />
                </button>
                <Link
                  href="/contact"
                  className="px-6 py-3.5 border border-[var(--color-bd-2)] text-white font-semibold rounded text-sm hover:bg-[var(--color-bg-2)] transition-colors text-center"
                >
                  Talk to Sales
                </Link>
              </div>
            </div>

            {/* Live preview mockup */}
            <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-5 md:p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-9 h-9 rounded-lg bg-[var(--color-yoga)]/15 flex items-center justify-center text-lg">
                  🧘
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold">Warrior II — Live Analysis</div>
                  <div className="text-xs text-[var(--color-muted)]">33 landmarks tracked</div>
                </div>
                <span className="w-2 h-2 rounded-full bg-[var(--color-yoga)] animate-pulse" />
              </div>
              <div className="space-y-3">
                {[
                  { label: "Hip Alignment", pct: 91 },
                  { label: "Arm Extension", pct: 84 },
                  { label: "Knee Position", pct: 78 },
                  { label: "Spine Lift", pct: 88 },
                ].map((bar) => (
                  <div key={bar.label} className="flex items-center gap-2.5 text-xs">
                    <span className="w-24 text-[var(--color-muted)] flex-shrink-0">{bar.label}</span>
                    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[var(--color-yoga)] rounded-full"
                        style={{ width: `${bar.pct}%` }}
                      />
                    </div>
                    <span className="w-8 text-right tabular-nums">{bar.pct}%</span>
                  </div>
                ))}
              </div>
              <div className="mt-5 px-3 py-2.5 bg-[var(--color-yoga)]/10 border border-[var(--color-yoga)]/30 rounded text-center">
                <span className="text-xs font-bold tracking-wider text-[var(--color-yoga)]">
                  ✓ CORRECT POSE — 88/100
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CRITERIA */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-3">
            What we analyse
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-4">
            Five criteria. Every pose.
          </h2>
          <p className="text-base text-[var(--color-muted)] max-w-xl leading-relaxed mb-12">
            The same biomechanical checks a certified instructor would make — automated and instant.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5">
            {CRITERIA.map((c) => (
              <div
                key={c.title}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 hover:border-[var(--color-yoga)]/40 transition-colors"
              >
                <div className="w-11 h-11 rounded-lg bg-[var(--color-yoga)]/10 flex items-center justify-center mb-4">
                  <c.Icon className="text-[var(--color-yoga)]" size={22} />
                </div>
                <h3 className="text-base font-bold mb-2">{c.title}</h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed">{c.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* POSE LIBRARY */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-10">
            <div>
              <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-3">
                Pose library
              </div>
              <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
                10+ poses ready to practise.
              </h2>
            </div>
            <div className="flex items-center gap-2 text-sm text-[var(--color-muted)]">
              <Eye size={16} />
              <span>More added monthly</span>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {POSES.map((p) => (
              <div
                key={p}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-4 md:p-5 text-center hover:border-[var(--color-yoga)]/40 hover:bg-[var(--color-bg-3)] transition-colors"
              >
                <div className="text-2xl md:text-3xl mb-2">🧘</div>
                <div className="text-xs md:text-sm font-semibold">{p}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-3">
            Process
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-12">
            From browser to live coach in under a minute.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--color-bd)] border border-[var(--color-bd)] rounded-lg overflow-hidden">
            {STEPS.map((s) => (
              <div key={s.num} className="bg-[var(--color-bg-2)] p-6 md:p-8">
                <div className="flex items-center justify-between mb-5">
                  <span className="text-xs font-bold tracking-widest text-[var(--color-dim)]">
                    {s.num}
                  </span>
                  <s.Icon className="text-[var(--color-yoga)]" size={20} />
                </div>
                <h3 className="text-lg font-bold mb-2">{s.title}</h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-5 md:px-12 py-16 md:py-24 text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
            Ready to fix your form?
          </h2>
          <p className="text-base md:text-lg text-[var(--color-muted)] mb-8 max-w-xl mx-auto leading-relaxed">
            Open your camera and start your first pose — free, no credit card needed.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              disabled
              className="px-8 py-3.5 bg-[var(--color-yoga)]/50 text-[var(--color-bg)] font-bold rounded text-sm cursor-not-allowed opacity-70 inline-flex items-center justify-center gap-2"
            >
              <Wrench size={16} /> Still Building…
            </button>
            <Link
              href="/pricing"
              className="px-8 py-3.5 border border-[var(--color-bd-2)] text-white font-semibold rounded text-sm hover:bg-[var(--color-bg-2)] transition-colors"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
