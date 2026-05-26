import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { POSTS } from "./posts";

export default function BlogPage() {
  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-5xl mx-auto">
        <div className="text-xs font-bold tracking-[2.5px] uppercase text-[var(--color-blue-accent)] mb-3">
          Blog
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-5">
          Notes from the team.
        </h1>
        <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-12 md:mb-16 max-w-2xl">
          Engineering deep-dives, coaching insights, and the occasional industry rant.
        </p>

        <div className="space-y-4">
          {POSTS.map((p, i) => (
            <Link
              key={p.slug}
              href={`/blog/${p.slug}`}
              className="block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-8 hover:border-[var(--color-bd-2)] hover:bg-[var(--color-bg-3)] transition-colors group"
            >
              <div className="flex flex-col md:flex-row md:items-start gap-4 md:gap-6">
                <div className="md:w-32 flex-shrink-0">
                  <div className="text-[10px] font-bold tracking-[2px] uppercase text-[var(--color-yoga)] mb-1">
                    {p.category}
                  </div>
                  <div className="text-xs text-[var(--color-muted)]">{p.date}</div>
                  <div className="text-xs text-[var(--color-muted)]">{p.readTime}</div>
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl md:text-2xl font-bold tracking-tight mb-2 group-hover:text-[var(--color-yoga)] transition-colors">
                    {p.title}
                  </h2>
                  <p className="text-sm md:text-base text-[var(--color-muted)] leading-relaxed mb-4">
                    {p.excerpt}
                  </p>
                  <span className="inline-flex items-center gap-2 text-sm font-bold group-hover:gap-3 transition-all">
                    Read post <ArrowRight size={14} />
                  </span>
                </div>
              </div>
              {i < POSTS.length - 1 && null}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
