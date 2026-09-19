/**
 * ShinyText — React Bits' sweeping highlight.
 *
 * A moving light band clipped to the glyphs. Pure CSS (see `rb-shiny` in
 * reactbits.css), so it costs nothing and stops on its own under a
 * reduced-motion preference.
 */
export default function ShinyText({ text, disabled = false, speed = 4, className = '' }) {
  return (
    <span
      className={`rb-shiny${disabled ? ' rb-shiny-off' : ''} ${className}`.trim()}
      style={{ '--rb-shiny-duration': `${speed}s` }}
    >
      {text}
    </span>
  )
}
