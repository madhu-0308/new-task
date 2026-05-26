import Link from "next/link";
import Image from "next/image";

const COLS = [
  {
    title: "Products",
    links: [
      { href: "/products/yoga", label: "Yoga AI Coach" },
      { href: "/products/cricket", label: "Cricket AI Coach" },
      { href: "/products", label: "All Products" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/about", label: "About" },
      { href: "/careers", label: "Careers" },
      { href: "/contact", label: "Contact" },
    ],
  },
  {
    title: "Resources",
    links: [
      { href: "/technology", label: "Technology" },
      { href: "/blog", label: "Blog" },
      { href: "/faq", label: "FAQ" },
      { href: "/pricing", label: "Pricing" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="bg-[var(--color-bg-1)] border-t border-[var(--color-bd)] px-5 md:px-12 py-12 md:py-16">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12 pb-10 border-b border-[var(--color-bd)]">
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="inline-block mb-4">
              <Image
                src="/logo.png"
                alt="Gaara AI"
                width={220}
                height={80}
                className="h-20 w-auto invert"
              />
            </Link>
            <p className="text-sm text-[var(--color-muted)] leading-relaxed max-w-xs">
              Custom AI coaching solutions powered by computer vision and deep learning.
            </p>
          </div>
          {COLS.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-bold tracking-widest uppercase text-[var(--color-dim)] mb-4">
                {col.title}
              </h4>
              <ul className="space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="text-sm text-[var(--color-muted)] hover:text-white transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="pt-6 flex flex-col md:flex-row md:justify-between items-start md:items-center gap-3 text-xs text-[var(--color-dim)]">
          <span>© {new Date().getFullYear()} Gaara AI. All rights reserved.</span>
          <div className="flex gap-5">
            <Link href="/privacy" className="hover:text-[var(--color-muted)]">Privacy</Link>
            <Link href="/terms" className="hover:text-[var(--color-muted)]">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
