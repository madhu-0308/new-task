import { Target, Eye, Users } from "lucide-react";

const VALUES = [
  {
    Icon: Target,
    title: "Mission",
    body: "Make professional-grade coaching accessible to every athlete and student through AI — anywhere, anytime, on any device.",
  },
  {
    Icon: Eye,
    title: "Vision",
    body: "A world where computer-vision coaching is as common as fitness trackers — helping millions improve technique safely.",
  },
  {
    Icon: Users,
    title: "Team",
    body: "ML engineers, biomechanics researchers, and coaches building the next generation of intelligent training tools.",
  },
];

export default function AboutPage() {
  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-4xl mx-auto">
        <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
          About
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-6">
          Building the future of AI coaching.
        </h1>
        <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-12 md:mb-20 max-w-2xl">
          Gaara AI was founded with a single belief: real-time biomechanical feedback shouldn&apos;t
          be a luxury reserved for elite athletes. We design AI coaching products that bring
          coach-grade analysis into every living room, gym, and academy.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
          {VALUES.map((v) => (
            <div
              key={v.title}
              className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-8"
            >
              <v.Icon className="text-[var(--color-yoga)]" size={28} />
              <h3 className="text-lg font-bold mt-4 mb-2">{v.title}</h3>
              <p className="text-sm text-[var(--color-muted)] leading-relaxed">{v.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-16 md:mt-24 grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-16">
          <div>
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-4">Our story</h2>
            <p className="text-sm md:text-base text-[var(--color-muted)] leading-relaxed">
              We started Gaara AI to solve a problem we faced ourselves — practising technique at
              home with no way to know if our form was right. Today our products help athletes,
              students, and clients across yoga, cricket, and beyond.
            </p>
          </div>
          <div>
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-4">What we do</h2>
            <p className="text-sm md:text-base text-[var(--color-muted)] leading-relaxed">
              We build custom computer-vision coaching products for clients — and license our
              flagship Yoga and Cricket platforms to studios, academies, and direct-to-consumer
              wellness apps.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
