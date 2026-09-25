import { lazy, Suspense, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Icon } from '../components/ui'
import { useDocumentTitle } from '../lib/title'
import { TIER_COLORS, TIER_ORDER } from '../theme'
import AnimatedContent from '../components/reactbits/AnimatedContent'
import CountUp from '../components/reactbits/CountUp'
import GradientText from '../components/reactbits/GradientText'
import ShinyText from '../components/reactbits/ShinyText'
import SplitText from '../components/reactbits/SplitText'
import ProfileCard from '../components/reactbits/ProfileCard'
import SpotlightCard from '../components/reactbits/SpotlightCard'
import TiltedCard from '../components/reactbits/TiltedCard'

/**
 * Public landing page.
 *
 * Everything here renders without an API call: this is the one route an
 * unauthenticated visitor sees, and it must not depend on a backend that may
 * be asleep. The figures quoted are the model's held-out test metrics, kept in
 * one place below so they cannot drift apart across the copy.
 *
 * Presentation is built from the React Bits primitives in
 * components/reactbits — aurora shader, split headline, spotlight cards,
 * scroll glides. Every one of them degrades to plain static markup under
 * `prefers-reduced-motion`, and the aurora also degrades when WebGL is
 * unavailable, so none of the copy depends on an animation running.
 *
 * The vivid palette is deliberately scoped to `.lp` and stops at the sign-in
 * boundary. The application behind it keeps the restrained clinical palette
 * and the colour-blindness-validated risk tiers; a marketing gradient has no
 * business rendering next to a discharge-risk read.
 */

const METRICS = [
  { value: 0.61, decimals: 2, suffix: ' d', label: 'Length-of-stay error', note: 'RMSE, held-out split' },
  { value: 91.9, decimals: 1, suffix: '%', label: 'Risk-tier accuracy', note: 'five-tier classifier' },
  { value: 50, decimals: 0, prefix: '<', suffix: ' ms', label: 'Per prediction', note: 'including explanation' },
]

const FEATURES = [
  {
    icon: 'patient',
    title: 'Per-patient forecasts',
    body: 'Predict length of stay at admission from seven routine fields, with a five-tier discharge-risk read alongside it.',
    glow: 'var(--lp-aqua)',
  },
  {
    icon: 'dashboard',
    title: 'Bed capacity planning',
    body: 'Project occupancy up to 60 days ahead across the whole cohort, so the ward sees a squeeze before it arrives.',
    glow: 'var(--lp-cyan)',
  },
  {
    icon: 'alert',
    title: 'Explained, not asserted',
    body: 'Every prediction ships with the SHAP factors behind it, in plain language. No number appears without its reasoning.',
    glow: 'var(--lp-violet)',
    ink: '#fff',
  },
  {
    icon: 'upload',
    title: 'Validated ingestion',
    body: 'Upload a CSV or Excel extract and get specific, actionable errors rather than a silent failure halfway through.',
    glow: 'var(--lp-pink)',
    ink: '#fff',
  },
]

const STEPS = [
  { n: '01', title: 'Upload an extract', body: 'Drop in a CSV of admissions. Every column is validated against the schema before anything is stored.' },
  { n: '02', title: 'Score the cohort', body: 'The model predicts length of stay and discharge risk for each record, logging every prediction for audit.' },
  { n: '03', title: 'Plan and export', body: 'Read the dashboard, drill into any patient, and download a PDF report for the capacity meeting.' },
]

/**
 * The aurora is the only thing on this page that needs a WebGL library, and
 * it is decoration layered over a gradient that already stands on its own.
 * Split out, `ogl` leaves the entry bundle and is fetched after the hero has
 * painted — and a visitor who has asked for reduced motion never renders the
 * component at all, so they never download it either.
 */
const Aurora = lazy(() => import('../components/reactbits/Aurora'))

/**
 * The model's inputs and outputs, for the "under the hood" section.
 *
 * Mirrored from ml/schema.py. Seven routine admission fields in, three things
 * out — that ratio is the point of the section, so both lists are spelled out
 * rather than summarised.
 */
const PIPELINE_INPUTS = [
  'Age',
  'Gender',
  'Admission type',
  'Diagnosis group',
  'Department',
  'Comorbidity count',
  'Prior admissions',
]

const PIPELINE_OUTPUTS = [
  {
    icon: 'clock',
    title: 'Length of stay',
    body: 'A gradient-boosted regressor predicts the stay in days, to within 0.61 days RMSE on held-out data.',
  },
  {
    icon: 'alert',
    title: 'Discharge-risk tier',
    body: 'A separate classifier places the admission in one of five tiers, from Very Low to Very High.',
  },
  {
    icon: 'compare',
    title: 'The reasoning',
    body: 'A SHAP explainer returns the factors that pushed the estimate up or down, ranked and in plain language.',
  },
]

/** The two clinical roles, mirrored from backend/roles.py. */
const ROLES = [
  {
    icon: 'patient',
    label: 'Doctor',
    lede: 'Works one admission at a time.',
    accent: 'var(--lp-cyan)',
    points: [
      'Score an admission from seven routine fields',
      'Read the SHAP drivers behind the stay',
      'Track a personal caseload towards discharge',
      'Export a per-patient PDF for the ward round',
    ],
  },
  {
    icon: 'chart',
    label: 'Analyst',
    lede: 'Works the whole cohort.',
    accent: 'var(--lp-violet)',
    points: [
      'Upload and validate an admissions extract',
      'Project ward occupancy up to 60 days ahead',
      'Monitor whether the model is still trustworthy',
      'Export a capacity-planning PDF for the meeting',
    ],
  },
]

/** What the thing is actually built out of. */
const STACK = [
  { group: 'Model', items: ['XGBoost', 'scikit-learn', 'SHAP', 'pandas'] },
  { group: 'API', items: ['Flask', 'JWT auth', 'SQLAlchemy', 'Alembic'] },
  { group: 'Interface', items: ['React', 'Vite', 'Recharts', 'React Bits'] },
  { group: 'Data', items: ['SQLite', 'MySQL', 'CSV / Excel ingest', 'ReportLab'] },
]

/** The people who built it. */
const TEAM = [
  {
    name: 'Ravi Kishan',
    role: 'Machine learning & backend',
    detail: 'Model training, the SHAP explanation layer, and the Flask API behind it.',
    initials: 'RK',
    accent: '#6366f1',
    accentTo: '#22d3ee',
    tags: ['XGBoost', 'SHAP', 'Flask'],
  },
  {
    name: 'Utsav Chauhan',
    role: 'Frontend & design system',
    detail: 'The React interface, the charting layer, and the design tokens both themes run on.',
    initials: 'UC',
    accent: '#14b8a6',
    accentTo: '#6366f1',
    tags: ['React', 'Recharts', 'Design'],
  },
  {
    name: 'Abhishek Anand',
    role: 'Data pipeline & reporting',
    detail: 'Dataset validation, the ingestion contract, and the generated PDF reports.',
    initials: 'AA',
    accent: '#ec4899',
    accentTo: '#f59e0b',
    tags: ['Pandas', 'Validation', 'PDF'],
  },
]

/** Colour ramp for the hero shader — aqua through violet, left to right. */
const AURORA_STOPS = ['#14E0C0', '#7C5CFF', '#22D3EE']

/**
 * The hero visual: a stylised 14-day occupancy forecast.
 *
 * Plain elements and CSS rather than a chart library — the figures are
 * illustrative, not data, and a visitor who may never sign in should not pay
 * to download Recharts for a picture. Marked aria-hidden for the same reason:
 * there is nothing here for a screen reader that the copy does not say.
 */
function HeroChart() {
  const bars = [58, 64, 61, 72, 78, 74, 83, 88, 84, 91, 86, 79, 74, 69]
  const capacity = 92

  return (
    <div className="lp-hero-visual" aria-hidden="true">
      <TiltedCard max={7}>
        <div className="lp-visual-card">
          <div className="lp-visual-head">
            <div>
              <div className="lp-visual-title">Projected occupancy</div>
              <div className="lp-visual-sub">Next 14 days</div>
            </div>
            <span className="lp-chip">
              <span className="lp-chip-dot" />
              Live
            </span>
          </div>

          <div className="lp-bars">
            {bars.map((height, index) => (
              <div className="lp-bar-slot" key={index}>
                <div
                  className={`lp-bar${height >= capacity - 6 ? ' lp-bar-warn' : ''}`}
                  style={{ '--h': `${height}%`, '--i': index }}
                />
              </div>
            ))}
            <div className="lp-capacity-line">
              <span>capacity</span>
            </div>
          </div>

          <div className="lp-visual-foot">
            {TIER_ORDER.map((tier) => (
              <span className="lp-tier" key={tier}>
                <span className="lp-tier-dot" style={{ background: TIER_COLORS[tier] }} />
                {tier}
              </span>
            ))}
          </div>
        </div>
      </TiltedCard>

      <div className="lp-float lp-float-a">
        <div className="lp-float-label">Predicted stay</div>
        <div className="lp-float-value tnum">
          18.6<span className="lp-float-unit">days</span>
        </div>
      </div>

      <div className="lp-float lp-float-b">
        <div className="lp-float-label">Discharge risk</div>
        <div className="lp-float-tier" style={{ background: TIER_COLORS.Moderate }}>
          Moderate
        </div>
      </div>
    </div>
  )
}

function Metric({ metric }) {
  const decimals = metric.decimals ?? 0

  return (
    <SpotlightCard className="lp-metric" spotlightColor="rgba(34, 211, 238, 0.16)">
      <div className="lp-metric-value tnum">
        {metric.prefix ?? ''}
        <CountUp to={metric.value} decimals={decimals} />
        <span className="lp-metric-suffix">{metric.suffix}</span>
      </div>
      <div className="lp-metric-label">{metric.label}</div>
      <div className="lp-metric-note">{metric.note}</div>
    </SpotlightCard>
  )
}

export default function Landing() {
  const { user } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  const [wantsMotion] = useState(
    () => !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
  )

  useDocumentTitle('Hospital length-of-stay forecasting')

  // The bar starts transparent over the dark hero and only takes on the
  // page's own surface once it has left it — a themed glass bar sitting on
  // the aurora reads as a seam across the top of the page.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const primaryHref = user ? '/dashboard' : '/login'
  const primaryLabel = user ? 'Open dashboard' : 'Sign in'

  return (
    <div className="lp">
      <header className={`lp-nav${scrolled ? ' lp-nav-solid' : ''}`}>
        <div className="lp-nav-inner">
          <div className="brand" style={{ margin: 0 }}>
            <div className="brand-mark lp-brand-mark">
              <Icon name="pulse" size={17} />
            </div>
            <div>
              <div className="brand-name">Recovery Forecast</div>
              <div className="brand-sub">BED MANAGEMENT</div>
            </div>
          </div>

          <nav className="lp-nav-links">
            <a href="#features">Features</a>
            <a href="#model">The model</a>
            <a href="#how">How it works</a>
            <a href="#team">Team</a>
            <Link className="lp-btn lp-btn-primary lp-btn-sm" to={primaryHref}>
              {primaryLabel}
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <section className="lp-stage">
          {wantsMotion && (
            <Suspense fallback={null}>
              <Aurora colorStops={AURORA_STOPS} amplitude={0.9} blend={0.34} speed={0.8} />
            </Suspense>
          )}
          <div className="lp-stage-scrim" aria-hidden="true" />
          <div className="lp-stage-grid" aria-hidden="true" />
          <div className="lp-stage-fade" aria-hidden="true" />

          <div className="lp-hero">
            <div className="lp-hero-copy">
              <span className="lp-eyebrow">
                <span className="lp-chip-dot" />
                <ShinyText text="Length-of-stay forecasting" speed={5} />
              </span>

              <h1>
                <SplitText text="Know the bed is needed" delay={26} duration={0.75} />
                <GradientText className="lp-hero-accent" animationSpeed={9}>
                  before it is.
                </GradientText>
              </h1>

              <AnimatedContent distance={26} duration={0.8} delay={0.25} threshold={0}>
                <p className="lp-lede">
                  Predict how long each admission will stay, see where occupancy
                  peaks over the next fortnight, and get the reasoning behind every
                  number — so discharge planning starts on day one, not day five.
                </p>

                <div className="lp-cta-row">
                  <Link className="lp-btn lp-btn-primary lp-btn-lg" to={primaryHref}>
                    {primaryLabel}
                    <Icon name="arrow-right" size={15} />
                  </Link>
                  <a className="lp-btn lp-btn-glass lp-btn-lg" href="#how">
                    How it works
                  </a>
                </div>
              </AnimatedContent>
            </div>

            <AnimatedContent
              distance={40}
              duration={1}
              delay={0.15}
              scale={0.96}
              blur={6}
              threshold={0}
            >
              <HeroChart />
            </AnimatedContent>
          </div>
        </section>

        <section className="lp-metrics" aria-label="Model performance">
          {METRICS.map((metric, index) => (
            <AnimatedContent key={metric.label} distance={34} delay={index * 0.08}>
              <Metric metric={metric} />
            </AnimatedContent>
          ))}
        </section>

        <section className="lp-section" id="features">
          <AnimatedContent distance={30}>
            <div className="lp-section-head">
              <span className="lp-kicker">Why it earns the screen</span>
              <h2>
                Built around the decision,{' '}
                <GradientText animationSpeed={10}>not the model</GradientText>
              </h2>
              <p>
                A forecast nobody trusts changes nothing. Every part of this
                system is shaped by what a bed manager has to justify in the
                morning meeting.
              </p>
            </div>
          </AnimatedContent>

          <div className="lp-features">
            {FEATURES.map((feature, index) => (
              <AnimatedContent
                key={feature.title}
                distance={36}
                delay={index * 0.07}
                blur={4}
              >
                <SpotlightCard
                  as="article"
                  className="lp-feature"
                  spotlightColor="rgba(124, 92, 255, 0.16)"
                  style={{
                    '--lp-feature-glow': feature.glow,
                    ...(feature.ink ? { '--lp-feature-ink': feature.ink } : {}),
                  }}
                >
                  <span className="lp-feature-icon">
                    <Icon name={feature.icon} size={17} />
                  </span>
                  <h3>{feature.title}</h3>
                  <p>{feature.body}</p>
                </SpotlightCard>
              </AnimatedContent>
            ))}
          </div>
        </section>

        <section className="lp-section lp-section-alt" id="how">
          <AnimatedContent distance={30}>
            <div className="lp-section-head">
              <span className="lp-kicker">How it works</span>
              <h2>Three steps to a staffed plan</h2>
              <p>From a raw admissions extract to a PDF you can take into a meeting.</p>
            </div>
          </AnimatedContent>

          {/* Each step animates as the <li> itself: an <ol> may only contain
              list items, so the wrapper cannot be a div. */}
          <ol className="lp-steps">
            {STEPS.map((step, index) => (
              <AnimatedContent
                as="li"
                key={step.n}
                className="lp-step"
                distance={44}
                direction="horizontal"
                delay={index * 0.1}
              >
                <span className="lp-step-n">{step.n}</span>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </AnimatedContent>
            ))}
          </ol>
        </section>

        {/* --- under the hood ------------------------------------------ */}
        <section className="lp-section" id="model">
          <AnimatedContent distance={30}>
            <div className="lp-section-head">
              <span className="lp-kicker">Under the hood</span>
              <h2>
                Seven fields in,{' '}
                <GradientText animationSpeed={10}>three answers out</GradientText>
              </h2>
              <p>
                No free text, no notes, no imaging — only fields a hospital
                already records at admission. That is what makes it deployable
                against a routine extract rather than a research dataset.
              </p>
            </div>
          </AnimatedContent>

          <div className="lp-pipeline">
            <AnimatedContent distance={34} direction="horizontal" reverse>
              <div className="lp-pipe-inputs">
                <div className="lp-pipe-label">Admission record</div>
                <ul>
                  {PIPELINE_INPUTS.map((field) => (
                    <li key={field}>
                      <Icon name="check" size={13} />
                      {field}
                    </li>
                  ))}
                </ul>
              </div>
            </AnimatedContent>

            <AnimatedContent distance={20} delay={0.1} className="lp-pipe-core">
              <div className="lp-pipe-engine">
                <span className="lp-pipe-pulse" aria-hidden="true" />
                <Icon name="pulse" size={22} />
                <div className="lp-pipe-engine-name">Gradient-boosted ensemble</div>
                <div className="lp-pipe-engine-note">trained on 24,000 admissions</div>
              </div>
            </AnimatedContent>

            <div className="lp-pipe-outputs">
              {PIPELINE_OUTPUTS.map((output, index) => (
                <AnimatedContent
                  key={output.title}
                  distance={34}
                  direction="horizontal"
                  delay={index * 0.08}
                >
                  <SpotlightCard
                    className="lp-pipe-out"
                    spotlightColor="rgba(99, 102, 241, 0.14)"
                  >
                    <span className="lp-pipe-out-icon">
                      <Icon name={output.icon} size={16} />
                    </span>
                    <div>
                      <h3>{output.title}</h3>
                      <p>{output.body}</p>
                    </div>
                  </SpotlightCard>
                </AnimatedContent>
              ))}
            </div>
          </div>
        </section>

        {/* --- the two roles -------------------------------------------- */}
        <section className="lp-section lp-section-alt" id="roles">
          <AnimatedContent distance={30}>
            <div className="lp-section-head">
              <span className="lp-kicker">Who it is for</span>
              <h2>Two roles, one hospital, opposite ends</h2>
              <p>
                A doctor and a bed manager need different answers from the same
                forecast. Each account sees only its own half — enforced by the
                API, not hidden in the interface.
              </p>
            </div>
          </AnimatedContent>

          <div className="lp-roles">
            {ROLES.map((role, index) => (
              <AnimatedContent key={role.label} distance={38} delay={index * 0.1}>
                <SpotlightCard
                  className="lp-role"
                  spotlightColor="rgba(34, 211, 238, 0.14)"
                  style={{ '--lp-role-accent': role.accent }}
                >
                  <div className="lp-role-head">
                    <span className="lp-role-icon">
                      <Icon name={role.icon} size={18} />
                    </span>
                    <div>
                      <h3>{role.label}</h3>
                      <p>{role.lede}</p>
                    </div>
                  </div>
                  <ul className="lp-role-points">
                    {role.points.map((point) => (
                      <li key={point}>
                        <Icon name="check" size={13} />
                        {point}
                      </li>
                    ))}
                  </ul>
                </SpotlightCard>
              </AnimatedContent>
            ))}
          </div>
        </section>

        {/* --- stack ---------------------------------------------------- */}
        <section className="lp-section" id="stack">
          <AnimatedContent distance={30}>
            <div className="lp-section-head">
              <span className="lp-kicker">Built with</span>
              <h2>An honest, boring stack</h2>
              <p>
                Nothing exotic. A trained model, a REST API in front of it, and
                a single-page interface — each piece chosen because it is the
                obvious one, not the interesting one.
              </p>
            </div>
          </AnimatedContent>

          <div className="lp-stack">
            {STACK.map((column, index) => (
              <AnimatedContent key={column.group} distance={30} delay={index * 0.07}>
                <div className="lp-stack-col">
                  <div className="lp-stack-group">{column.group}</div>
                  <ul>
                    {column.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </AnimatedContent>
            ))}
          </div>
        </section>

        {/* --- team ----------------------------------------------------- */}
        <section className="lp-section lp-team-section" id="team">
          <AnimatedContent distance={30}>
            <div className="lp-section-head lp-section-head-center">
              <span className="lp-kicker">The team</span>
              <h2>
                Built at{' '}
                <GradientText className="lp-vit" animationSpeed={9}>
                  VIT Vellore
                </GradientText>
              </h2>
              <p>
                Three of us, one problem: a ward that finds out it is full on
                the morning it happens.
              </p>
            </div>
          </AnimatedContent>

          <div className="lp-team">
            {TEAM.map((member, index) => (
              <AnimatedContent
                key={member.name}
                distance={42}
                delay={index * 0.1}
                blur={5}
              >
                <ProfileCard {...member} />
              </AnimatedContent>
            ))}
          </div>
        </section>

        <section className="lp-final">
          <div className="lp-final-glow" aria-hidden="true" />
          <AnimatedContent distance={30} className="lp-final-inner">
            <h2>See it on your own admissions data.</h2>
            <p>
              Sign in with the demo account and upload the bundled sample extract —
              the full dashboard is two clicks away.
            </p>
            <Link className="lp-btn lp-btn-primary lp-btn-lg" to={primaryHref}>
              {primaryLabel}
              <Icon name="arrow-right" size={15} />
            </Link>
          </AnimatedContent>
        </section>
      </main>

      <footer className="lp-footer">
        <span>
          Healthcare Recovery Forecast — Ravi Kishan, Utsav Chauhan and
          Abhishek Anand, VIT Vellore
        </span>
        <span className="lp-footer-note">
          Decision support only — not a substitute for clinical judgement.
        </span>
      </footer>
    </div>
  )
}
