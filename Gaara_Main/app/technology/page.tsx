import Link from "next/link";
import { Camera, Layers, Brain, Zap, ArrowRight, ChevronRight } from "lucide-react";

const PIPELINE = [
  { Icon: Camera, label: "Camera", sub: "30fps webcam", color: "var(--color-blue-accent)" },
  { Icon: Layers, label: "Pose Extraction", sub: "MediaPipe Holistic", color: "var(--color-yoga)" },
  { Icon: Brain, label: "LSTM", sub: "30-frame window", color: "var(--color-cricket)" },
  { Icon: Zap, label: "Feedback", sub: "<250ms response", color: "var(--color-orange-accent)" },
];

const FEATURES_TABLE = [
  { source: "Pose landmarks", count: "33 × 4", total: "132", desc: "x, y, z + visibility per body keypoint" },
  { source: "Hand landmarks", count: "21 × 3 × 2", total: "126", desc: "x, y, z per point, both hands" },
  { source: "Face mesh", count: "468 × 3", total: "1,404", desc: "x, y, z per facial landmark" },
];

const LSTM_LAYERS = [
  { name: "Input Layer", shape: "(30, 1662)", desc: "30 time steps × 1,662 features per frame" },
  { name: "LSTM 1", shape: "64 units", desc: "ReLU activation, return sequences" },
  { name: "LSTM 2", shape: "128 units", desc: "ReLU activation, return sequences" },
  { name: "LSTM 3", shape: "64 units", desc: "ReLU activation, final state only" },
  { name: "Dense", shape: "64 units", desc: "ReLU activation" },
  { name: "Dense", shape: "32 units", desc: "ReLU activation" },
  { name: "Output", shape: "Softmax", desc: "Action class probabilities" },
];

const STACK = [
  { name: "MediaPipe Holistic", role: "Pose & landmark extraction" },
  { name: "TensorFlow / Keras", role: "LSTM model training & inference" },
  { name: "FastAPI", role: "Python backend serving predictions" },
  { name: "Next.js + React", role: "Frontend coaching interface" },
  { name: "Firebase Auth", role: "User authentication" },
  { name: "Vercel + EC2", role: "Edge frontend, GPU backend" },
];

export default function TechnologyPage() {
  return (
    <>
      {/* HERO */}
      <section className="relative pt-28 pb-12 md:pt-40 md:pb-20 px-5 md:px-12 overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_60%_at_50%_30%,rgba(79,144,248,0.10),transparent_60%)]" />
        <div className="max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 text-[10px] md:text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-5">
            <span className="w-6 h-px bg-[var(--color-blue-accent)]" />
            Technology
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.05] mb-5">
            How the AI sees you,
            <br />
            <span className="text-[var(--color-blue-accent)]">frame by frame.</span>
          </h1>
          <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed max-w-2xl">
            Gaara AI combines real-time computer vision with sequence-aware deep learning — the
            same techniques used in research labs, optimised to run live in your browser.
          </p>
        </div>
      </section>

      {/* PIPELINE FLOW */}
      <section className="px-5 md:px-12 py-12 md:py-16 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
            The pipeline
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-10">
            Camera to coaching cue in four stages.
          </h2>
          <div className="flex flex-col md:flex-row md:items-stretch md:justify-between gap-3 md:gap-2">
            {PIPELINE.map((p, i) => (
              <div key={p.label} className="flex md:flex-col items-center gap-3 md:gap-0 flex-1">
                <div className="flex md:flex-col items-center md:flex-1 md:w-full">
                  <div
                    className="w-12 h-12 md:w-16 md:h-16 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: `${p.color}20`, border: `1px solid ${p.color}40` }}
                  >
                    <p.Icon size={22} style={{ color: p.color }} />
                  </div>
                  <div className="ml-4 md:ml-0 md:mt-3 md:text-center">
                    <div className="text-sm font-bold">{p.label}</div>
                    <div className="text-xs text-[var(--color-muted)]">{p.sub}</div>
                  </div>
                </div>
                {i < PIPELINE.length - 1 && (
                  <ChevronRight
                    className="text-[var(--color-dim)] flex-shrink-0 rotate-90 md:rotate-0 md:self-center md:mx-1"
                    size={20}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MEDIAPIPE */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-start">
          <div>
            <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-3">
              Stage 1 · Pose Extraction
            </div>
            <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-5">
              MediaPipe Holistic.
            </h2>
            <p className="text-base text-[var(--color-muted)] leading-relaxed mb-5">
              Every frame is fed through Google&apos;s MediaPipe Holistic model, which extracts
              full-body landmarks in real time on commodity hardware.
            </p>
            <p className="text-base text-[var(--color-muted)] leading-relaxed">
              The output is a complete biomechanical snapshot — body, hands, and face — ready to be
              consumed by the recognition model.
            </p>
          </div>
          <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-8 space-y-4">
            <div className="text-xs font-bold tracking-widest uppercase text-[var(--color-dim)] mb-3">
              Per Frame
            </div>
            {[
              { label: "Body landmarks", val: "33 keypoints", color: "var(--color-yoga)" },
              { label: "Hand landmarks", val: "21 × 2 hands", color: "var(--color-cricket)" },
              { label: "Face mesh", val: "468 points", color: "var(--color-blue-accent)" },
              { label: "Inference rate", val: "30fps", color: "var(--color-orange-accent)" },
            ].map((row) => (
              <div
                key={row.label}
                className="flex items-center justify-between pb-3 border-b border-[var(--color-bd)] last:border-0 last:pb-0"
              >
                <span className="text-sm text-[var(--color-muted)]">{row.label}</span>
                <span className="text-sm font-bold tabular-nums" style={{ color: row.color }}>
                  {row.val}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURE ENGINEERING */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
            Stage 2 · Feature Engineering
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-5">
            1,662 features per frame.
          </h2>
          <p className="text-base text-[var(--color-muted)] leading-relaxed max-w-2xl mb-12">
            Landmarks are flattened into a single feature vector consumed by the LSTM. Each row below
            shows how the dimensions add up.
          </p>
          <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg overflow-hidden">
            <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-3 border-b border-[var(--color-bd)] text-xs font-bold tracking-widest uppercase text-[var(--color-dim)]">
              <div className="col-span-3">Source</div>
              <div className="col-span-2">Count</div>
              <div className="col-span-2 text-right">Total Dims</div>
              <div className="col-span-5">Description</div>
            </div>
            {FEATURES_TABLE.map((f) => (
              <div
                key={f.source}
                className="px-5 md:px-6 py-4 border-b border-[var(--color-bd)] last:border-0 grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4"
              >
                <div className="md:col-span-3 text-sm font-semibold">{f.source}</div>
                <div className="md:col-span-2 text-sm text-[var(--color-muted)] tabular-nums">
                  {f.count}
                </div>
                <div className="md:col-span-2 md:text-right text-base md:text-lg font-extrabold text-[var(--color-cricket)] tabular-nums">
                  {f.total}
                </div>
                <div className="md:col-span-5 text-xs md:text-sm text-[var(--color-muted)]">
                  {f.desc}
                </div>
              </div>
            ))}
            <div className="px-5 md:px-6 py-4 bg-[var(--color-bg-3)] grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4">
              <div className="md:col-span-7 text-sm font-bold">Total per frame</div>
              <div className="md:col-span-2 md:text-right text-xl font-extrabold text-white tabular-nums">
                1,662
              </div>
              <div className="md:col-span-3 text-xs text-[var(--color-muted)] md:text-right">
                fed into LSTM
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* LSTM */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-3">
            Stage 3 · Recognition
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-5">
            LSTM neural network.
          </h2>
          <p className="text-base text-[var(--color-muted)] leading-relaxed max-w-2xl mb-12">
            A Long Short-Term Memory network processes sequences of 30 frames — capturing the
            temporal dynamics that distinguish a correct movement from a flawed one.
          </p>
          <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg overflow-hidden">
            {LSTM_LAYERS.map((l, i) => (
              <div
                key={i}
                className={`px-5 md:px-6 py-4 grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4 ${
                  i < LSTM_LAYERS.length - 1 ? "border-b border-[var(--color-bd)]" : ""
                } ${i === LSTM_LAYERS.length - 1 ? "bg-[var(--color-cricket)]/5" : ""}`}
              >
                <div className="md:col-span-1 text-xs font-bold tabular-nums text-[var(--color-dim)]">
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div className="md:col-span-3 text-sm font-bold">{l.name}</div>
                <div className="md:col-span-3 text-sm font-mono text-[var(--color-cricket)] tabular-nums">
                  {l.shape}
                </div>
                <div className="md:col-span-5 text-xs md:text-sm text-[var(--color-muted)]">
                  {l.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REAL-TIME LOOP */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-orange-accent)] mb-3">
            Stage 4 · Real-Time Loop
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-12 max-w-3xl">
            Sliding window inference at 30fps.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              {
                title: "Sliding window",
                body: "The latest 30 frames are kept in a rolling buffer. Each new frame replaces the oldest, giving the model continuous context.",
                color: "var(--color-yoga)",
              },
              {
                title: "Throttled inference",
                body: "Predictions run every 250ms — fast enough to feel instant, slow enough to avoid burning compute when the body isn't moving.",
                color: "var(--color-cricket)",
              },
              {
                title: "Stable detection",
                body: "A shot or pose is only confirmed after 3 consecutive frames pass the confidence threshold — preventing flicker from noisy poses.",
                color: "var(--color-blue-accent)",
              },
            ].map((c) => (
              <div
                key={c.title}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6"
              >
                <div className="w-1 h-8 rounded-full mb-4" style={{ background: c.color }} />
                <h3 className="text-base font-bold mb-2">{c.title}</h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed">{c.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TECH STACK */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
            Stack
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-12">
            What it&apos;s built on.
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {STACK.map((s) => (
              <div
                key={s.name}
                className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-5 hover:border-[var(--color-bd-2)] transition-colors"
              >
                <div className="text-sm font-bold mb-1.5">{s.name}</div>
                <div className="text-xs text-[var(--color-muted)]">{s.role}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-5 md:px-12 py-16 md:py-24 text-center bg-[var(--color-bg-1)] border-t border-[var(--color-bd)]">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
            Want to license this stack?
          </h2>
          <p className="text-base md:text-lg text-[var(--color-muted)] mb-8 max-w-xl mx-auto leading-relaxed">
            We license our pose-recognition pipeline for custom sports and wellness products. Talk to us about your use case.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/contact"
              className="px-8 py-3.5 bg-white text-[var(--color-bg)] font-bold rounded text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
            >
              Talk to Sales <ArrowRight size={16} />
            </Link>
            <Link
              href="/products"
              className="px-8 py-3.5 border border-[var(--color-bd-2)] text-white font-semibold rounded text-sm hover:bg-[var(--color-bg-2)] transition-colors"
            >
              View Products
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
