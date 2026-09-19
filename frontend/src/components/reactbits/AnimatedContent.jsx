import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

/**
 * AnimatedContent — React Bits' scroll-in wrapper.
 *
 * Glides its children in from `direction` once they reach the viewport, and
 * then leaves them alone (`once`). Under a reduced-motion preference it
 * renders a plain wrapper and never touches the element, so the content is
 * on screen and fully opaque from the first paint.
 */
export default function AnimatedContent({
  children,
  distance = 48,
  direction = 'vertical',
  reverse = false,
  duration = 0.9,
  ease = 'power3.out',
  initialOpacity = 0,
  scale = 1,
  blur = 0,
  threshold = 0.15,
  delay = 0,
  className = '',
  as: Tag = 'div',
}) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      return undefined
    }

    const axis = direction === 'horizontal' ? 'x' : 'y'
    const offset = reverse ? -distance : distance

    const ctx = gsap.context(() => {
      gsap.set(el, {
        [axis]: offset,
        opacity: initialOpacity,
        scale,
        filter: blur ? `blur(${blur}px)` : 'none',
      })

      gsap.to(el, {
        [axis]: 0,
        opacity: 1,
        scale: 1,
        filter: 'blur(0px)',
        duration,
        ease,
        delay,
        scrollTrigger: {
          trigger: el,
          start: `top ${(1 - threshold) * 100}%`,
          once: true,
        },
      })
    }, ref)

    return () => ctx.revert()
  }, [
    distance,
    direction,
    reverse,
    duration,
    ease,
    initialOpacity,
    scale,
    blur,
    threshold,
    delay,
  ])

  return (
    <Tag className={className} ref={ref}>
      {children}
    </Tag>
  )
}
