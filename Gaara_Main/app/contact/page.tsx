"use client";

import { useState, FormEvent } from "react";

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(true);
  }

  return (
    <div className="px-5 md:px-12 pt-28 md:pt-40 pb-16 md:pb-24">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          {/* LEFT — Title + tagline + contact details */}
          <div className="lg:sticky lg:top-32">
            <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight leading-[1.05] mb-6 md:mb-8">
              Talk to a Human
            </h1>
            <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-2 max-w-md">
              Ask us how AI coaching can transform your studio, academy, or product.
            </p>
            <p className="text-base md:text-lg text-[var(--color-muted)] leading-relaxed mb-10 md:mb-14 max-w-md">
              Ask us how we&apos;ve helped athletes go from beginner to coach-grade form.
            </p>

            <div className="space-y-8">
              <div>
                <h3 className="text-base md:text-lg font-bold mb-3">Phone</h3>
                <div className="space-y-1.5">
                  <a
                    href="tel:+919346766404"
                    className="block text-base text-[var(--color-muted)] hover:text-white transition-colors"
                  >
                    +91 93467 66404
                  </a>
                  <a
                    href="tel:+916300892887"
                    className="block text-base text-[var(--color-muted)] hover:text-white transition-colors"
                  >
                    +91 63008 92887
                  </a>
                  <a
                    href="tel:+916305952162"
                    className="block text-base text-[var(--color-muted)] hover:text-white transition-colors"
                  >
                    +91 63059 52162
                  </a>
                </div>
              </div>

              <div>
                <h3 className="text-base md:text-lg font-bold mb-3">Email</h3>
                <a
                  href="mailto:admin@gaaraai.com"
                  className="text-base text-[var(--color-muted)] hover:text-white transition-colors break-all"
                >
                  admin@gaaraai.com
                </a>
              </div>

              <div>
                <h3 className="text-base md:text-lg font-bold mb-3">Location</h3>
                <span className="text-base text-[var(--color-muted)]">IIT Madras, Chennai</span>
              </div>
            </div>
          </div>

          {/* RIGHT — Form */}
          <div>
            {submitted ? (
              <div className="bg-[var(--color-bg-2)] border border-[var(--color-cricket)]/40 rounded-lg p-10 md:p-12 text-center">
                <div className="text-[var(--color-cricket)] text-5xl mb-4">✓</div>
                <h3 className="text-2xl font-bold mb-3">Thanks for reaching out!</h3>
                <p className="text-sm md:text-base text-[var(--color-muted)] max-w-sm mx-auto">
                  We&apos;ll get back to you within one business day.
                </p>
              </div>
            ) : (
              <form onSubmit={onSubmit} className="space-y-6">
                <Field label="Name" name="firstName" placeholder="Your name" required />
                <Field label="Last name" name="lastName" placeholder="Your last name" required />
                <Field
                  label="Email"
                  name="email"
                  type="email"
                  placeholder="Your email address"
                  required
                />
                <div>
                  <label className="block text-sm font-semibold mb-2.5">
                    Message<span className="text-[var(--color-yoga)]">*</span>
                  </label>
                  <textarea
                    name="message"
                    rows={6}
                    required
                    placeholder="Enter your message"
                    className="w-full bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg px-4 py-3.5 text-sm md:text-base text-white placeholder:text-[var(--color-dim)] outline-none focus:border-[var(--color-yoga)] resize-none transition-colors"
                  />
                </div>
                <button
                  type="submit"
                  className="px-8 py-3.5 bg-[var(--color-yoga)] text-[var(--color-bg)] font-bold rounded-lg text-sm md:text-base hover:opacity-90 transition-opacity"
                >
                  Submit
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  name,
  type = "text",
  placeholder,
  required = false,
}: {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm font-semibold mb-2.5">
        {label}
        {required && <span className="text-[var(--color-yoga)]">*</span>}
      </label>
      <input
        type={type}
        name={name}
        required={required}
        placeholder={placeholder}
        className="w-full bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg px-4 py-3.5 text-sm md:text-base text-white placeholder:text-[var(--color-dim)] outline-none focus:border-[var(--color-yoga)] transition-colors"
      />
    </div>
  );
}
