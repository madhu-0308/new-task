"use client";

import { useState } from "react";
import { ArrowRight, X, Wrench } from "lucide-react";
import RequireAuth from "@/auth/RequireAuth";
import { useAuth } from "@/auth/AuthProvider";

const SERVICES = [
  {
    name: "Yoga AI Coach",
    desc: "Real-time pose correction across hip alignment, balance, arm extension, spine, and weight distribution.",
    href: null, // not ready yet — shows "Still building..."
    color: "var(--color-yoga)",
    bg: "linear-gradient(135deg, #180b3a 0%, #2d1060 55%, #0a0620 100%)",
    emoji: "🧘",
    badge: "Yoga",
  },
  {
    name: "Cricket AI Coach",
    desc: "Shot-specific coaching for the cover drive and pull shot. LSTM-powered batting recognition with step-by-step cues.",
    href: "https://cric2-fawn.vercel.app",
    color: "var(--color-cricket)",
    bg: "linear-gradient(135deg, #001d10 0%, #004520 55%, #000d07 100%)",
    emoji: "🏏",
    badge: "Cricket",
  },
];

export default function SelectServicePage() {
  return (
    <RequireAuth>
      <SelectServiceContent />
    </RequireAuth>
  );
}

function SelectServiceContent() {
  const { user } = useAuth();
  const firstName = user?.displayName?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "there";
  const [showBuildingModal, setShowBuildingModal] = useState<string | null>(null);

  return (
    <div className="px-5 md:px-12 pt-28 md:pt-32 pb-16 md:pb-24 min-h-[80vh]">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-10 md:mb-14">
          <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
            Welcome, {firstName}
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-4">
            Choose your service.
          </h1>
          <p className="text-base md:text-lg text-[var(--color-muted)] max-w-xl mx-auto leading-relaxed">
            Pick a coaching platform to get started. You can switch between them anytime.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6">
          {SERVICES.map((s) => {
            const content = (
              <>
                <div
                  className="h-40 md:h-48 flex items-center justify-center text-7xl md:text-8xl"
                  style={{ background: s.bg }}
                >
                  {s.emoji}
                </div>
                <div className="p-6 md:p-8">
                  <div
                    className="text-[10px] font-bold tracking-[2px] uppercase mb-3"
                    style={{ color: s.color }}
                  >
                    {s.badge}
                  </div>
                  <h3 className="text-2xl font-extrabold tracking-tight mb-3">{s.name}</h3>
                  <p className="text-sm text-[var(--color-muted)] leading-relaxed mb-5">{s.desc}</p>
                  <span
                    className="inline-flex items-center gap-2 text-sm font-bold group-hover:gap-3 transition-all"
                    style={{ color: s.color }}
                  >
                    Launch {s.badge} <ArrowRight size={16} />
                  </span>
                </div>
              </>
            );

            const className =
              "group block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg overflow-hidden hover:border-[var(--color-bd-2)] transition-colors text-left w-full";

            if (s.href) {
              return (
                <a key={s.name} href={s.href} className={className}>
                  {content}
                </a>
              );
            }
            return (
              <button
                key={s.name}
                onClick={() => setShowBuildingModal(s.badge)}
                className={className}
              >
                {content}
              </button>
            );
          })}
        </div>
      </div>

      {/* Still building modal */}
      {showBuildingModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-5 bg-black/70 backdrop-blur-sm"
          onClick={() => setShowBuildingModal(null)}
        >
          <div
            className="bg-[var(--color-bg-2)] border border-[var(--color-bd-2)] rounded-lg max-w-md w-full p-8 text-center relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowBuildingModal(null)}
              className="absolute top-4 right-4 text-[var(--color-muted)] hover:text-white"
              aria-label="Close"
            >
              <X size={20} />
            </button>
            <div className="w-16 h-16 rounded-full bg-[var(--color-yoga)]/10 border border-[var(--color-yoga)]/30 flex items-center justify-center mx-auto mb-5">
              <Wrench className="text-[var(--color-yoga)]" size={28} />
            </div>
            <h3 className="text-2xl font-extrabold tracking-tight mb-3">Still building…</h3>
            <p className="text-sm md:text-base text-[var(--color-muted)] leading-relaxed mb-6">
              {showBuildingModal} AI Coach is in active development. We&apos;ll notify you the
              moment it&apos;s ready to use.
            </p>
            <button
              onClick={() => setShowBuildingModal(null)}
              className="w-full py-3 bg-white text-[var(--color-bg)] font-bold rounded text-sm hover:opacity-90 transition-opacity"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
