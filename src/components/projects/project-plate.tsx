import Image from "next/image";

type PlateProps = {
  src: string;
  alt: string;
  width: number;
  height: number;
  href?: string;
  sizes: string;
  label: string;
};

/**
 * A screenshot as a plate. It wipes in once, and the image drifts slightly inside its
 * frame as you scroll, driven by a CSS view timeline rather than a scroll listener.
 */
export function ProjectPlate({ src, alt, width, height, href, sizes, label }: PlateProps) {
  const body = (
    <span className="plate-shift block">
      <Image src={src} alt={alt} width={width} height={height} sizes={sizes} className="block h-auto w-full" />
    </span>
  );

  if (!href) {
    return (
      <div data-reveal="wipe" className="plate relative">
        {body}
      </div>
    );
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      aria-label={`${label}, opens in a new tab`}
      data-reveal="wipe"
      className="plate relative block"
    >
      {body}
    </a>
  );
}
