"use client";

import Image from "next/image";
import { useRef, useState, ReactNode } from "react";

interface Props {
  videoSrc: string;
  posterSrc: string;
  alt: string;
  side: "left" | "right";
  children: ReactNode;
  className?: string;
}

export default function HoverVideoBg({
  videoSrc,
  posterSrc,
  alt,
  side,
  children,
  className = "",
}: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);

  return (
    <div
      className={`relative min-h-[60vh] md:min-h-[70vh] flex items-center overflow-hidden ${className}`}
      onMouseEnter={() => {
        ref.current?.play().catch(() => {});
        setPlaying(true);
      }}
      onMouseLeave={() => {
        if (ref.current) {
          ref.current.pause();
          ref.current.currentTime = 0;
        }
        setPlaying(false);
      }}
    >
      <Image
        src={posterSrc}
        alt={alt}
        fill
        className={`object-cover transition-opacity duration-500 ${
          playing ? "opacity-0" : "opacity-100"
        }`}
      />
      <video
        ref={ref}
        src={videoSrc}
        muted
        loop
        playsInline
        preload="metadata"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${
          playing ? "opacity-100" : "opacity-0"
        }`}
      />
      <div
        className={`absolute inset-0 ${
          side === "left" ? "bg-gradient-to-r" : "bg-gradient-to-l"
        } from-[var(--color-bg-1)] via-[var(--color-bg-1)]/70 to-transparent pointer-events-none`}
      />
      {children}
    </div>
  );
}
