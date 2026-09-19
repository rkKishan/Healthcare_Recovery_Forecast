import { useEffect, useRef } from 'react'
import gsap from 'gsap'

/**
 * TiltedCard — React Bits' pointer-parallax tilt.
 *
 * Rotates the card toward the cursor on two axes. gsap's quickTo is used
 * rather than a tween per event: it reuses one interpolator, so a fast
 * mousemove does not queue up dozens of competing animations.
 *
 * Pointer-driven and therefore mouse-only by nature; touch and keyboard users
 * get the card exactly as laid out, which is the whole content.
 */
export default function TiltedCard({
  children,
  className = '',
  max = 9,
  scale = 1.015,
  perspective = 1000,
}) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      return undefined
    }
    // A coarse pointer cannot hover, and the tilt would only fire as a jolt
    // on tap.
    if (!window.matchMedia?.('(hover: hover) and (pointer: fine)').matches) {
      return undefined
    }

    const setX = gsap.quickTo(el, 'rotationY', { duration: 0.5, ease: 'power3.out' })
    const setY = gsap.quickTo(el, 'rotationX', { duration: 0.5, ease: 'power3.out' })
    const setS = gsap.quickTo(el, 'scale', { duration: 0.5, ease: 'power3.out' })

    const onMove = (event) => {
      const rect = el.getBoundingClientRect()
      const px = (event.clientX - rect.left) / rect.width - 0.5
      const py = (event.clientY - rect.top) / rect.height - 0.5
      setX(px * max * 2)
      setY(-py * max * 2)
    }
    const onEnter = () => setS(scale)
    const onLeave = () => {
      setX(0)
      setY(0)
      setS(1)
    }

    el.addEventListener('mousemove', onMove)
    el.addEventListener('mouseenter', onEnter)
    el.addEventListener('mouseleave', onLeave)

    return () => {
      el.removeEventListener('mousemove', onMove)
      el.removeEventListener('mouseenter', onEnter)
      el.removeEventListener('mouseleave', onLeave)
      gsap.set(el, { clearProps: 'transform' })
    }
  }, [max, scale])

  return (
    <div className="rb-tilt-scene" style={{ perspective: `${perspective}px` }}>
      <div className={`rb-tilt ${className}`.trim()} ref={ref}>
        {children}
      </div>
    </div>
  )
}
