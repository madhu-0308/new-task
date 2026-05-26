import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { getPost, POSTS } from "../posts";

export function generateStaticParams() {
  return POSTS.map((p) => ({ slug: p.slug }));
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) notFound();

  const others = POSTS.filter((p) => p.slug !== slug).slice(0, 2);

  return (
    <article className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-3xl mx-auto">
        <Link
          href="/blog"
          className="text-xs text-[var(--color-muted)] hover:text-white inline-flex items-center gap-1.5 mb-8"
        >
          ← All posts
        </Link>

        <div className="flex flex-wrap items-center gap-3 mb-5 text-xs">
          <span className="font-bold tracking-[2px] uppercase text-[var(--color-yoga)]">
            {post.category}
          </span>
          <span className="text-[var(--color-dim)]">·</span>
          <span className="text-[var(--color-muted)]">{post.date}</span>
          <span className="text-[var(--color-dim)]">·</span>
          <span className="text-[var(--color-muted)]">{post.readTime}</span>
        </div>

        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight mb-10 md:mb-14">
          {post.title}
        </h1>

        <div className="space-y-5 md:space-y-6 text-base md:text-lg text-[var(--color-muted)] leading-relaxed">
          {post.body.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        <div className="mt-16 pt-10 border-t border-[var(--color-bd)]">
          <h2 className="text-xs font-bold tracking-widest uppercase text-[var(--color-dim)] mb-5">
            Keep reading
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {others.map((p) => (
              <Link
                key={p.slug}
                href={`/blog/${p.slug}`}
                className="block bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-5 hover:border-[var(--color-bd-2)] hover:bg-[var(--color-bg-3)] transition-colors group"
              >
                <div className="text-[10px] font-bold tracking-[2px] uppercase text-[var(--color-yoga)] mb-2">
                  {p.category}
                </div>
                <div className="text-base font-bold mb-2 group-hover:text-[var(--color-yoga)] transition-colors">
                  {p.title}
                </div>
                <span className="inline-flex items-center gap-2 text-xs font-bold text-[var(--color-muted)] group-hover:text-white">
                  Read <ArrowRight size={12} />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}
