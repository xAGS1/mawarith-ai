import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
export function SectionHeading({
  eyebrow,
  title,
  description,
  icon,
  href,
  linkText,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  icon: ReactNode;
  href?: string;
  linkText?: string;
}) {
  return (
    <div className="section-heading">
      <div className="heading-main">
        <span className="heading-icon" aria-hidden="true">
          {icon}
        </span>
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h2>{title}</h2>
          <p className="section-description">{description}</p>
        </div>
      </div>
      {href && (
        <a className="text-link" href={href}>
          {linkText}
          <ArrowLeft size={16} aria-hidden="true" />
        </a>
      )}
    </div>
  );
}
