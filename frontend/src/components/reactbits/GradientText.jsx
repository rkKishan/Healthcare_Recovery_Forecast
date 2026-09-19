/**
 * GradientText — React Bits' animated gradient type.
 *
 * The gradient is painted onto the text itself and slides across it. `colors`
 * is repeated end-to-start by the caller when a seamless loop is wanted; this
 * component only lays it down and moves it.
 */
export default function GradientText({
  children,
  className = '',
  colors = null,
  animationSpeed = 8,
}) {
  // With no colours the stylesheet supplies the ramp, which is how the
  // landing page gets a gradient deep enough to read on white and bright
  // enough to read on near-black without two copies of every call site.
  return (
    <span
      className={`rb-gradient-text ${className}`.trim()}
      style={{
        ...(colors
          ? { backgroundImage: `linear-gradient(90deg, ${colors.join(', ')})` }
          : null),
        animationDuration: `${animationSpeed}s`,
      }}
    >
      {children}
    </span>
  )
}
