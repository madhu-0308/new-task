import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  Activity,
  Cpu,
  LineChart,
  Quote,
} from "lucide-react";
import { POSTS } from "./blog/posts";
import HoverVideoBg from "@/components/HoverVideoBg";

const TECH = [
  {
    Icon: Activity,
    cat: "Pose Tracking",
    title: "MediaPipe Holistic",
    body: "33 body landmarks, 21 hand points, and 468 face markers tracked in real time at 30fps.",
    href: "/technology",
    color: "var(--color-yoga)",
    image: "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=800&q=80&auto=format",
  },
  {
    Icon: Cpu,
    cat: "Recognition",
    title: "LSTM Neural Network",
    body: "30-frame sliding window classifies movements and returns coaching cues in milliseconds.",
    href: "/technology",
    color: "var(--color-cricket)",
    image: "https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=800&q=80&auto=format",
  },
  {
    Icon: LineChart,
    cat: "Insight",
    title: "Form Scoring",
    body: "Quantified form scores with criteria breakdown and progress history per athlete.",
    href: "/technology",
    color: "var(--color-blue-accent)",
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80&auto=format",
  },
];

export default function HomePage() {
  return (
    <>
      {/* 1 — CINEMATIC HERO */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <Image
            src="https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=2000&q=80&auto=format"
            alt=""
            fill
            priority
            className="object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-bg)]/70 via-[var(--color-bg)]/85 to-[var(--color-bg)]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_30%,rgba(167,139,250,0.12),transparent_60%)]" />
        </div>
        <div className="relative max-w-7xl mx-auto px-5 md:px-12 w-full pt-20 pb-12">
          <div className="text-[10px] md:text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-6">
            Innovating in Coaching
          </div>
          <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight leading-[1.02] mb-6 max-w-5xl">
            AI coaching,
            <br />
            built for athletes
            <br />
            who demand the best.
          </h1>
          <p className="text-base md:text-xl text-[var(--color-muted)] max-w-2xl leading-relaxed mb-10">
            Real-time pose analysis, shot recognition, and instant feedback —
            trusted across yoga and cricket, expanding to every sport.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href="/products"
              className="px-7 py-3.5 bg-white text-[var(--color-bg)] font-bold rounded text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
            >
              Explore Products <ArrowRight size={16} />
            </Link>
            <Link
              href="/contact"
              className="px-7 py-3.5 border border-[var(--color-bd-2)] text-white font-semibold rounded text-sm hover:bg-[var(--color-bg-2)] transition-colors text-center"
            >
              Talk to Sales
            </Link>
          </div>
        </div>
      </section>

      {/* 2 — STATS BAND */}
      <section className="border-y border-[var(--color-bd)] bg-[var(--color-bg-1)]">
        <div className="max-w-7xl mx-auto px-5 md:px-12 py-10 md:py-12">
          <p className="text-center text-sm md:text-base text-[var(--color-muted)] mb-6 md:mb-8">
            Coaching <strong className="text-white">10+ poses</strong> across{" "}
            <strong className="text-white">2 sports</strong>, processing{" "}
            <strong className="text-white">1,662 features per frame</strong> at{" "}
            <strong className="text-white">30fps</strong>.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[var(--color-bd)] border border-[var(--color-bd)] rounded-lg overflow-hidden">
            {[
              { n: "1,662", l: "Features per Frame" },
              { n: "30fps", l: "Real-Time Analysis" },
              { n: "<250ms", l: "Inference Time" },
              { n: "10+", l: "Pose & Shot Models" },
            ].map((s) => (
              <div key={s.l} className="bg-[var(--color-bg-1)] py-6 md:py-8 px-4 text-center">
                <div className="text-2xl md:text-4xl font-extrabold tracking-tight">{s.n}</div>
                <div className="text-xs md:text-sm text-[var(--color-muted)] mt-1.5">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3 — OUR TECHNOLOGIES */}
      <section className="px-5 md:px-12 py-16 md:py-24 bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <div className="max-w-7xl mx-auto">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
            Our Technologies
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3 max-w-3xl">
            Three systems, working in concert.
          </h2>
          <p className="text-base md:text-lg text-[var(--color-muted)] max-w-2xl leading-relaxed mb-12">
            From effortless biomechanics to instant feedback — every Gaara AI product is engineered on the same core stack.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
            {TECH.map((t) => (
              <Link
                key={t.cat}
                href={t.href}
                className="group block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg overflow-hidden hover:border-[var(--color-bd-2)] transition-colors"
              >
                <div className="relative h-44 md:h-52">
                  <Image
                    src={t.image}
                    alt=""
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-bg-2)] via-[var(--color-bg-2)]/40 to-transparent" />
                  <div className="absolute bottom-4 left-5 flex items-center gap-2">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center"
                      style={{ background: `${t.color}25`, border: `1px solid ${t.color}50` }}
                    >
                      <t.Icon size={18} style={{ color: t.color }} />
                    </div>
                    <span
                      className="text-[10px] font-bold tracking-[2px] uppercase"
                      style={{ color: t.color }}
                    >
                      {t.cat}
                    </span>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-lg md:text-xl font-bold mb-2 group-hover:text-white transition-colors">
                    {t.title}
                  </h3>
                  <p className="text-sm text-[var(--color-muted)] leading-relaxed mb-4">{t.body}</p>
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[var(--color-muted)] group-hover:text-white">
                    Learn more <ArrowRight size={12} />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* 6 — LATEST FROM BLOG */}
      <section className="px-5 md:px-12 py-16 md:py-24">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-10 md:mb-12">
            <div>
              <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
                Latest News
              </div>
              <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
                From the team.
              </h2>
            </div>
            <Link
              href="/blog"
              className="text-sm font-semibold text-[var(--color-muted)] hover:text-white inline-flex items-center gap-1.5"
            >
              View all posts <ArrowRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
            {POSTS.slice(0, 3).map((p) => (
              <Link
                key={p.slug}
                href={`/blog/${p.slug}`}
                className="group block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-7 hover:border-[var(--color-bd-2)] hover:bg-[var(--color-bg-3)] transition-colors"
              >
                <div className="flex items-center gap-3 mb-4 text-xs">
                  <span className="font-bold tracking-[2px] uppercase text-[var(--color-yoga)]">
                    {p.category}
                  </span>
                  <span className="text-[var(--color-dim)]">·</span>
                  <span className="text-[var(--color-muted)]">{p.readTime}</span>
                </div>
                <h3 className="text-lg md:text-xl font-bold tracking-tight mb-3 group-hover:text-[var(--color-yoga)] transition-colors">
                  {p.title}
                </h3>
                <p className="text-sm text-[var(--color-muted)] leading-relaxed line-clamp-3 mb-5">
                  {p.excerpt}
                </p>
                <span className="inline-flex items-center gap-1.5 text-xs font-bold group-hover:gap-2.5 transition-all">
                  Read post <ArrowRight size={12} />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* 7 — SPORT SHOWCASE (Yoga full-bleed) */}
      <section className="bg-[var(--color-bg-1)] border-y border-[var(--color-bd)]">
        <HoverVideoBg
          posterSrc="https://images.unsplash.com/photo-1545389336-cf090694435e?w=2000&q=80&auto=format"
          videoSrc="https://videos.pexels.com/video-files/3327752/3327752-hd_1920_1080_24fps.mp4"
          alt="Yoga"
          side="left"
        >
          <div className="relative z-10 max-w-7xl mx-auto px-5 md:px-12 w-full py-16 md:py-24">
            <div className="text-[10px] font-bold tracking-[2.5px] uppercase text-[var(--color-yoga)] mb-4">
              Yoga · AI Coaching
            </div>
            <h3 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] mb-5 max-w-2xl">
              Yoga form,
              <br />
              corrected in real time.
            </h3>
            <p className="text-base md:text-lg text-[var(--color-muted)] max-w-md mb-8">
              5 biomechanical criteria. 10+ poses. Coach-grade feedback from any browser.
            </p>
            <Link
              href="/products/yoga"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-[var(--color-yoga)] text-[var(--color-bg)] font-bold rounded text-sm hover:opacity-90 transition-opacity"
            >
              Explore Yoga <ArrowRight size={16} />
            </Link>
          </div>
        </HoverVideoBg>

        {/* Cricket full-bleed (mirrored) */}
        <HoverVideoBg
          posterSrc="https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=2000&q=80&auto=format"
          videoSrc="https://videos.pexels.com/video-files/11755921/11755921-uhd_2732_1440_60fps.mp4"
          alt="Cricket"
          side="right"
        >
          <div className="relative z-10 max-w-7xl mx-auto px-5 md:px-12 w-full py-16 md:py-24 flex justify-end">
            <div className="text-left md:text-right max-w-xl">
              <div className="text-[10px] font-bold tracking-[2.5px] uppercase text-[var(--color-cricket)] mb-4">
                Cricket · Batting Coach
              </div>
              <h3 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] mb-5">
                Batting,
                <br />
                analysed at 30fps.
              </h3>
              <p className="text-base md:text-lg text-[var(--color-muted)] mb-8 md:ml-auto md:max-w-md">
                LSTM-powered shot recognition for cover drive and pull shot — frame-by-frame coaching cues.
              </p>
              <Link
                href="/products/cricket"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-[var(--color-cricket)] text-[#001d10] font-bold rounded text-sm hover:opacity-90 transition-opacity"
              >
                Explore Cricket <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </HoverVideoBg>

        {/* INDUSTRY LEADERS */}
        <div className="px-5 md:px-12 py-16 md:py-24 border-t border-[var(--color-bd)]">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-4">
                Supported by{" "}
                <span className="text-[var(--color-blue-accent)]">Industry Leaders</span>
              </h2>
              <p className="text-base md:text-lg text-[var(--color-muted)] max-w-2xl mx-auto leading-relaxed">
                Our technology is recognised and supported by premier institutions and industry programmes.
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5">
              {[
                { name: "IIT Madras", sub: "Founding Institution" },
                { name: "Nirmaan", sub: "Pre-Incubator, IITM" },
                { name: "NVIDIA Inception", sub: "Program Member" },
                { name: "AWS for Startups", sub: "Activate Partner" },
              ].map((s) => (
                <div
                  key={s.name}
                  className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-5 md:p-7 flex flex-col items-center justify-center text-center min-h-[140px] md:min-h-[160px] hover:border-[var(--color-bd-2)] hover:bg-[var(--color-bg-3)] transition-colors"
                >
                  <div className="text-base md:text-lg font-extrabold tracking-tight mb-1">
                    {s.name}
                  </div>
                  <div className="text-[10px] md:text-xs font-semibold tracking-widest uppercase text-[var(--color-dim)]">
                    {s.sub}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 8 — WORLD CLASS PARTNERSHIPS */}
      <section className="px-5 md:px-12 py-20 md:py-32">
        <div className="max-w-4xl mx-auto text-center">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-12 md:mb-16">
            World Class Partnerships
          </div>
          <Quote className="text-[var(--color-yoga)]/40 mx-auto mb-8" size={48} />
          <blockquote className="text-2xl md:text-4xl lg:text-5xl font-bold tracking-tight leading-snug mb-12 italic">
            &ldquo;Gaara AI represents the next leap in democratising biomechanics — bringing
            coach-grade analysis into the hands of every athlete.&rdquo;
          </blockquote>
          <div className="flex flex-col items-center gap-1">
            <div className="text-base font-bold">IIT Madras Faculty</div>
            <div className="text-sm text-[var(--color-muted)]">
              Mentor, Nirmaan Pre-Incubator
            </div>
          </div>
        </div>
      </section>


    </>
  );
}
