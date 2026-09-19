import { useRef } from 'react'

/**
 * SpotlightCard — React Bits' cursor-tracked glow.
 *
 * Writes the pointer position into two custom properties; the radial
 * highlight itself is a CSS pseudo-element that reads them. Nothing here
 * re-renders React, which is what keeps a grid of these smooth on mousemove.
 */
export default function SpotlightCard({
  children,
  className = '',
  spotlightColor = 'rgba(255, 255, 255, 0.22)',
  as: Tag = 'div',
  style,
  ...rest
}) {
  const ref = useRef(null)

  const onMouseMove = (event) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty('--rb-x', `${event.clientX - rect.left}px`)
    el.style.setProperty('--rb-y', `${event.clientY - rect.top}px`)
    el.style.setProperty('--rb-spot-opacity', '1')
  }

  const onMouseLeave = () => {
    ref.current?.style.setProperty('--rb-spot-opacity', '0')
  }

  return (
    <Tag
      className={`rb-spotlight ${className}`.trim()}
      ref={ref}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      style={{ '--rb-spot': spotlightColor, ...style }}
      {...rest}
    >
      {children}
    </Tag>
  )
}
