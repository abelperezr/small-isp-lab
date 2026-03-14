import Link from "@docusaurus/Link";

export default function HeroSection({
  kicker = "Small ISP Lab",
  title,
  subtitle,
  primaryCta,
  secondaryCta,
}) {
  return (
    <section className="hero-section">
      <span className="hero-orb a" aria-hidden="true" />
      <span className="hero-orb b" aria-hidden="true" />

      <div className="hero-content">
        <span className="hero-kicker">{kicker}</span>
        <h1 className="hero-title">{title}</h1>
        <p className="hero-subtitle">{subtitle}</p>

        <div className="hero-actions">
          <Link className="btn-hero-primary" to={primaryCta.to}>
            {primaryCta.label}
          </Link>
          <Link className="btn-hero-secondary" to={secondaryCta.to}>
            {secondaryCta.label}
          </Link>
        </div>
      </div>
    </section>
  );
}
