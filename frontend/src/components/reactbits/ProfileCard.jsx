import { useCallback, useEffect, useRef } from 'react'

/**
 * ProfileCard — React Bits' holographic 3D card.
 *
 * The card rotates toward the pointer on two axes while a holographic sheen
 * and a glare highlight track the same position, and the contents sit on
 * their own translateZ planes so they parallax against the card face rather
 * than riding flat on it. That depth is the whole effect; without it a tilt
 * reads as a wobble.
 *
 * Everything is driven through CSS custom properties written straight to the
 * node inside a rAF, so a pointer moving across a row of these costs no React
 * renders at all. On a coarse pointer, or under a reduced-motion preference,
 * none of it runs and the card is simply a card.
 */

/** How far the card leans, in degrees, at the edges. */
const MAX_TILT = 14

export default function ProfileCard({
  name,
  role,
  detail,
  initials,
  accent = '#6366f1',
  accentTo = '#22d3ee',
  tags = [],
}) {
  const wrapRef = useRef(null)
  const cardRef = useRef(null)
  const frameRef = useRef(0)

  const write = useCallback((x, y, rect) => {
    const card = cardRef.current
    if (!card) return

    // Normalised to -0.5..0.5 from the card's centre.
    const px = x / rect.width - 0.5
    const py = y / rect.height - 0.5

    card.style.setProperty('--rx', `${-py * MAX_TILT * 2}deg`)
    card.style.setProperty('--ry', `${px * MAX_TILT * 2}deg`)
    // Percentages for the glare and the holographic sweep.
    card.style.setProperty('--px', `${(x / rect.width) * 100}%`)
    card.style.setProperty('--py', `${(y / rect.height) * 100}%`)
    card.style.setProperty('--hx', `${50 + px * 120}%`)
  }, [])

  useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return undefined
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      return undefined
    }
    // A finger cannot hover, and the tilt would only ever fire as a jolt on tap.
    if (!window.matchMedia?.('(hover: hover) and (pointer: fine)').matches) {
      return undefined
    }

    const onMove = (event) => {
      const rect = wrap.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top
      cancelAnimationFrame(frameRef.current)
      frameRef.current = requestAnimationFrame(() => write(x, y, rect))
    }

    const onEnter = () => cardRef.current?.classList.add('rb-profile-live')
    const onLeave = () => {
      cancelAnimationFrame(frameRef.current)
      const card = cardRef.current
      if (!card) return
      card.classList.remove('rb-profile-live')
      card.style.setProperty('--rx', '0deg')
      card.style.setProperty('--ry', '0deg')
      card.style.setProperty('--hx', '50%')
    }

    wrap.addEventListener('pointermove', onMove)
    wrap.addEventListener('pointerenter', onEnter)
    wrap.addEventListener('pointerleave', onLeave)

    return () => {
      cancelAnimationFrame(frameRef.current)
      wrap.removeEventListener('pointermove', onMove)
      wrap.removeEventListener('pointerenter', onEnter)
      wrap.removeEventListener('pointerleave', onLeave)
    }
  }, [write])

  return (
    <div
      className="rb-profile-scene"
      ref={wrapRef}
      style={{ '--accent': accent, '--accent-to': accentTo }}
    >
      <article className="rb-profile" ref={cardRef}>
        {/* Decorative layers, painted under the content and above the face. */}
        <span className="rb-profile-holo" aria-hidden="true" />
        <span className="rb-profile-glare" aria-hidden="true" />

        <div className="rb-profile-body">
          <div className="rb-profile-avatar" aria-hidden="true">
            {initials}
          </div>
          <h3 className="rb-profile-name">{name}</h3>
          <p className="rb-profile-role">{role}</p>
          {detail && <p className="rb-profile-detail">{detail}</p>}

          {tags.length > 0 && (
            <ul className="rb-profile-tags">
              {tags.map((tag) => (
                <li key={tag}>{tag}</li>
              ))}
            </ul>
          )}
        </div>
      </article>
    </div>
  )
}
