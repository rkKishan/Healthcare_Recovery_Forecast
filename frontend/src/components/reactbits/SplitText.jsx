import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText as GSAPSplitText } from 'gsap/SplitText'

gsap.registerPlugin(ScrollTrigger, GSAPSplitText)

/**
 * SplitText — React Bits' headline entrance.
 *
 * Splits the text into characters (or words, or lines) and staggers them in
 * once the element scrolls into view. The split is reverted on unmount so the
 * DOM is handed back exactly as it came in — without that, a re-render would
 * split the already-split markup and multiply the spans.
 *
 * The element keeps its real text content at all times, so the split is
 * invisible to a screen reader and to text selection either way.
 */
export default function SplitText({
  text,
  className = '',
  delay = 40,
  duration = 0.8,
  ease = 'power3.out',
  splitType = 'chars',
  from = { opacity: 0, y: 32 },
  to = { opacity: 1, y: 0 },
  threshold = 0.25,
  tag = 'span',
  onComplete,
}) {
  const ref = useRef(null)
  const doneRef = useRef(onComplete)
  doneRef.current = onComplete

  useEffect(() => {
    const el = ref.current
    if (!el || !text) return undefined
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      return undefined
    }

    let split
    const ctx = gsap.context(() => {
      // Characters are always split out of words rather than out of the raw
      // text: each char becomes an inline-block, so without the enclosing
      // word element the browser wraps mid-word ("nee / ded").
      const type = splitType === 'chars' ? 'words,chars' : splitType
      split = new GSAPSplitText(el, {
        type,
        linesClass: 'rb-split-line',
        wordsClass: 'rb-split-word',
      })
      const targets =
        splitType === 'lines' ? split.lines
        : splitType === 'words' ? split.words
        : split.chars

      gsap.fromTo(
        targets,
        { ...from },
        {
          ...to,
          duration,
          ease,
          stagger: delay / 1000,
          scrollTrigger: {
            trigger: el,
            start: `top ${100 - threshold * 100}%`,
            once: true,
          },
          onComplete: () => doneRef.current?.(),
        },
      )
    }, ref)

    return () => {
      ctx.revert()
      split?.revert()
    }
  }, [text, delay, duration, ease, splitType, threshold, from, to])

  const Tag = tag
  return (
    <Tag className={`rb-split ${className}`.trim()} ref={ref}>
      {text}
    </Tag>
  )
}
