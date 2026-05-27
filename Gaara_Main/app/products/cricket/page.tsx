import Link from "next/link";
import { ArrowRight, Footprints, Activity, RotateCw, Eye, Hand, Camera, Zap, BarChart3, Target } from "lucide-react";

const CRITERIA = [
  {
    Icon: Footprints,
    title: "Stance & Foot Position",
    body: "Verifies balanced weight, parallel feet, and correct stance width before the shot is played.",
  },
  {
    Icon: Activity,
    title: "Front Knee Drive",
    body: "Measures whether the front knee is driving over the ball — collapsed knees indicate poor weight transfer.",
  },
  {
    Icon: RotateCw,
    title: "Hip Rotation",
    body: "Analyses full hip drive through the ball — incomplete rotation is the primary cause of weak shots.",
  },
  {
    Icon: Eye,
    title: "Head Position",
    body: "Tracks head stability over the ball throughout the shot — the most common cause of mis-hits in batting.",
  },
  {
    Icon: Hand,
    title: "Follow-through",
    body: "Confirms full bat extension and weight transfer at the end of the shot — the mark of a properly timed stroke.",
  },
];

const STEPS = [
  {
    Icon: Target,
    num: "01",
    title: "Pick your shot",
    body: "Play any shot in front of your camera. The AI identifies which shot it was and grades your form.",
  },
  {
    Icon: Camera,
    num: "02",
    title: "Take guard",
    body: "Allow camera access, take your stance, and play the shot. The AI tracks 33 body landmarks at 30fps.",
  },
  {
    Icon: BarChart3,
    num: "03",
    title: "Score and refine",
    body: "Every attempt scored out of 100 with a criteria breakdown. Build streaks and watch your form improve.",
  },
];

export default function CricketProductPage() {
  return (
    <>
      {/* HERO */}
      <section className="relative pt-28 pb-12 md:pt-40 md:pb-20 px-5 md:px-12 overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_60%_at_50%_30%,rgba(16,232,124,0.10),transparent_60%)]" />
        <div className="max-w-6xl mx-auto">
          <Link
            href="/products"
            className="text-xs text-[var(--color-muted)] hover:text-white inline-flex items-center gap-1.5 mb-6"
          >
            ← All products
          </Link>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 text-[10px] md:text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-5">
                <span className="w-6 h-px bg-[var(--color-cricket)]" />
                Cricket · Batting Coach
              </div>
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.05] mb-5">
                Batting technique,
                <br />
                <span className="text-[var(--color-cricket)]">analysed at 30fps.</span>
              </h1>
              <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-8 max-w-xl">
                LSTM-powered shot recognition breaks down your cover drive and pull shot frame by frame —
                with biomechanical feedback once exclusive to professional academies.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
                <Link
                  href="/products/cricket/coach"
                  className="px-6 py-3.5 bg-[var(--color-cricket)] text-[#001d10] font-bold rounded text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
                >
                  Start Batting <ArrowRight size={16} />
                </Link>
                <Link
                  href="/products/cricket/analyze"
                  className="px-6 py-3.5 bg-[var(--color-bg-3)] border border-[var(--color-cricket)]/40 text-[var(--color-cricket)] font-bold rounded text-sm flex items-center justify-center gap-2 hover:bg-[var(--color-cricket)]/10 transition-colors"
                >
                  🎬 Delivery Analyzer
                </Link>
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
                <div className="w-9 h-9 rounded-lg bg-[var(--color-cricket)]/15 flex items-center justify-center text-lg">
                  🏏
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold">Live Shot Analysis</div>
                  <div className="text-xs text-[var(--color-muted)]">LSTM · 30 frame window</div>
                </div>
                <span className="w-2 h-2 rounded-full bg-[var(--color-cricket)] animate-pulse" />
              </div>
              <div className="space-y-3">
                {[
                  { label: "Front Knee Bend", pct: 88, color: "var(--color-cricket)" },
                  { label: "Arm Extension", pct: 72, color: "var(--color-orange-accent)" },
                  { label: "Head Position", pct: 94, color: "var(--color-cricket)" },
                  { label: "Hip Rotation", pct: 81, color: "var(--color-cricket)" },
                ].map((bar) => (
                  <div key={bar.label} className="flex items-center gap-2.5 text-xs">
                    <span className="w-24 text-[var(--color-muted)] flex-shrink-0">{bar.label}</span>
                    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${bar.pct}%`, background: bar.color }}
                      />
                    </div>
                    <span className="w-8 text-right tabular-nums">{bar.pct}%</span>
                  </div>
                ))}
              </div>
              <div className="mt-5 px-3 py-2.5 bg-[var(--color-orange-accent)]/10 border border-[var(--color-orange-accent)]/30 rounded text-center">
                <span className="text-xs font-bold tracking-wider text-[var(--color-orange-accent)]">
                  ▶ IN PROGRESS — Extend arms fully
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CRITERIA */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
            What we analyse
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-4">
            Five form checks. Every shot.
          </h2>
          <p className="text-base text-[var(--color-muted)] max-w-xl leading-relaxed mb-12">
            The same criteria a batting coach evaluates — measured mathematically, every single ball.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5">
            {CRITERIA.map((c) => (
              <div
                key={c.title}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 hover:border-[var(--color-cricket)]/40 transition-colors"
              >
                <div className="w-11 h-11 rounded-lg bg-[var(--color-cricket)]/10 flex items-center justify-center mb-4">
                  <c.Icon className="text-[var(--color-cricket)]" size={22} />
                </div>
                <h3 className="text-base font-bold mb-2">{c.title}</h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed">{c.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
            Process
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-12">
            From stance to score in under a minute.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--color-bd)] border border-[var(--color-bd)] rounded-lg overflow-hidden">
            {STEPS.map((s) => (
              <div key={s.num} className="bg-[var(--color-bg-2)] p-6 md:p-8">
                <div className="flex items-center justify-between mb-5">
                  <span className="text-xs font-bold tracking-widest text-[var(--color-dim)]">
                    {s.num}
                  </span>
                  <s.Icon className="text-[var(--color-cricket)]" size={20} />
                </div>
                <h3 className="text-lg font-bold mb-2">{s.title}</h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TECH STATS */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
            Under the hood
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-12 max-w-3xl">
            Built on real-time computer vision and deep learning.
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {[
              { n: "30fps", l: "Live Analysis" },
              { n: "<250ms", l: "Inference Time" },
              { n: "1,662", l: "Features per Frame" },
              { n: "30", l: "Frame LSTM Window" },
            ].map((s) => (
              <div
                key={s.l}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-5 md:p-6"
              >
                <div className="text-2xl md:text-3xl font-extrabold tracking-tight text-[var(--color-cricket)]">
                  {s.n}
                </div>
                <div className="text-xs md:text-sm text-[var(--color-muted)] mt-1.5">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-5 md:px-12 py-16 md:py-24 text-center bg-[var(--color-bg-1)] border-t border-[var(--color-bd)]">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
            Ready to refine your shots?
          </h2>
          <p className="text-base md:text-lg text-[var(--color-muted)] mb-8 max-w-xl mx-auto leading-relaxed">
            Pick up your bat, point a camera, and let the AI break down every stroke.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="https://cric2-fawn.vercel.app"
              className="px-8 py-3.5 bg-[var(--color-cricket)] text-[#001d10] font-bold rounded text-sm hover:opacity-90 transition-opacity"
            >
              Start Free
            </a>
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
