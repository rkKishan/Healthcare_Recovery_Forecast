import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'

/**
 * CountUp — React Bits' number roll, driven by gsap rather than a spring.
 *
 * Counts from `from` to `to` the first time the element is in view. The
 * animation is decoration but the figure is not, so it starts at the target
 * under a reduced-motion preference rather than at zero, and the tween is the
 * only thing that ever moves it away from a real value.
 */
export default function CountUp({
  to,
  from = 0,
  duration = 1.6,
  decimals = 0,
  prefix = '',
  suffix = '',
  separator = '',
  className = '',
}) {
  const reduced =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const [value, setValue] = useState(reduced ? to : from)
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el || reduced) return undefined

    const counter = { n: from }
    let tween

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return
        observer.disconnect()
        tween = gsap.to(counter, {
          n: to,
          duration,
          ease: 'power2.out',
          onUpdate: () => setValue(counter.n),
          onComplete: () => setValue(to),
        })
      },
      { threshold: 0.4 },
    )
    observer.observe(el)

    return () => {
      observer.disconnect()
      tween?.kill()
    }
  }, [to, from, duration, reduced])

  // Group the integer part only -- a naive replace on the whole string would
  // also punctuate the digits after the decimal point.
  const [whole, fraction] = value.toFixed(decimals).split('.')
  const grouped = separator
    ? whole.replace(/\B(?=(\d{3})+(?!\d))/g, separator)
    : whole
  const display = fraction ? `${grouped}.${fraction}` : grouped

  return (
    <span className={className} ref={ref}>
      {prefix}
      {display}
      {suffix}
    </span>
  )
}
