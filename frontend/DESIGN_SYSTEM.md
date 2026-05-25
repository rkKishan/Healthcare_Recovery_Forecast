# UI/UX Design System Specifications

## Visual Design Reference

### Color System

#### Primary Colors
```
Deep Navy (Primary Background)
Hex: #1A2B3C
RGB: 26, 43, 60
Usage: Main background, text, dark elements
```

```
Soft Teal (Accent)
Hex: #20B2AA
RGB: 32, 178, 170
Usage: CTAs, highlights, interactive elements, focus states
```

#### Secondary Colors
```
Soft Coral (Alert/Error)
Hex: #FF6B6B
RGB: 255, 107, 107
Usage: Error messages, validation failures
```

```
Success Green
Hex: #22C55E (Tailwind green-500)
RGB: 34, 197, 94
Usage: Success messages, valid form fields
```

#### Neutral Colors
```
White: #FFFFFF - Primary text
Gray 300: #D1D5DB - Secondary text
Gray 400: #9CA3AF - Tertiary text
Gray 600: #4B5563 - Disabled elements
Gray 700: #374151 - Borders
```

### Typography System

#### Font Families
```
Body: 'Inter', sans-serif
  - Weight: 300, 400, 500, 600, 700
  - Letter spacing: normal
  - Line height: 1.5 (body), 1.2 (headings)

Display/Headings: 'Montserrat', sans-serif
  - Weight: 700, 800
  - Use for: h1, h2, h3, strong statements
```

#### Font Sizes & Hierarchy

**Desktop Scale:**
```
h1: 56px / 3.5rem  (Montserrat 700)    → Landing headlines
h2: 48px / 3rem    (Montserrat 700)    → Section titles
h3: 32px / 2rem    (Montserrat 700)    → Subsection titles
h4: 24px / 1.5rem  (Montserrat 600)
p:  16px / 1rem    (Inter 400)         → Body text
small: 12px / 0.75rem (Inter 400)      → Helper text
```

**Mobile Scale:**
```
h1: 32px / 2rem
h2: 24px / 1.5rem
h3: 20px / 1.25rem
p:  14px / 0.875rem
small: 12px / 0.75rem
```

### Component Specifications

#### Glassmorphic Card

**Base Style:**
```css
background: rgba(255, 255, 255, 0.1);
backdrop-filter: blur(10px);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 12px;
box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
```

**Hover State:**
```css
background: rgba(255, 255, 255, 0.15);
border-color: rgba(32, 178, 170, 0.3);
transform: translateY(-2px);
box-shadow: 0 12px 48px rgba(31, 38, 135, 0.5);
transition: all 0.3s ease;
```

**Usage:**
- Auth forms
- Feature cards
- Modals
- Info boxes

#### Primary Button

**Base Style:**
```css
padding: 12px 24px;
background: linear-gradient(135deg, #20B2AA, #1aa89e);
color: #1A2B3C;
border-radius: 8px;
font-weight: 600;
border: none;
cursor: pointer;
box-shadow: 0 0 20px rgba(32, 178, 170, 0.3);
```

**Hover State:**
```css
transform: scale(1.05);
box-shadow: 0 0 30px rgba(32, 178, 170, 0.5);
```

**Active State:**
```css
transform: scale(0.95);
```

**Disabled State:**
```css
opacity: 0.5;
cursor: not-allowed;
transform: scale(1);
```

#### Input Fields

**Base Style:**
```css
background: rgba(255, 255, 255, 0.1);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 8px;
padding: 12px 16px;
color: #FFFFFF;
font-size: 14px;
backdrop-filter: blur(10px);
```

**Focus State:**
```css
border-color: #20B2AA;
ring: 2px solid rgba(32, 178, 170, 0.3);
outline: none;
```

**Valid State:**
```css
border-color: #22C55E;
ring: 2px solid rgba(34, 197, 94, 0.2);
```

**Invalid State:**
```css
border-color: #FF6B6B;
ring: 2px solid rgba(255, 107, 107, 0.2);
```

#### Role Selector Chip

**Unselected State:**
```css
background: rgba(75, 85, 99, 0.1);
border: 2px solid rgba(75, 85, 99, 0.5);
color: rgba(209, 213, 219, 0.8);
border-radius: 8px;
padding: 12px 16px;
cursor: pointer;
transition: all 0.3s ease;
```

**Selected State:**
```css
background: rgba(32, 178, 170, 0.3);
border: 2px solid #20B2AA;
color: #20B2AA;
```

**Hover State (Unselected):**
```css
border-color: #20B2AA;
background: rgba(32, 178, 170, 0.1);
color: #20B2AA;
```

### Spacing System

**Base Unit: 4px (Tailwind scale)**

```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
2xl: 48px
3xl: 64px
4xl: 80px
5xl: 96px
6xl: 128px
```

**Usage:**
```
Padding:       Use multiples of 4px (4, 8, 12, 16, 20, 24, 32)
Margin:        Use multiples of 4px (4, 8, 12, 16, 20, 24, 32)
Gap:           Use multiples of 4px (4, 8, 16, 24, 32)
Border Radius: 4px, 8px, 12px, 16px, 24px
Border Width:  1px, 2px
```

### Shadow & Elevation

```
Shallow:  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
Medium:   box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
Deep:     box-shadow: 0 12px 48px rgba(31, 38, 135, 0.5);
Glow:     box-shadow: 0 0 20px rgba(32, 178, 170, 0.3);
Glow-lg:  box-shadow: 0 0 50px rgba(32, 178, 170, 0.5);
```

### Animation Specifications

#### Transitions

**Standard Transition:**
```
Duration: 300ms
Easing: cubic-bezier(0.4, 0, 0.2, 1) [ease-in-out]
Properties: all
```

**Page Transitions:**
```
Duration: 300ms
Easing: easeInOut
Direction: fade in (opacity), slide up (y: 20px → 0px)
```

**Component Entrance (Staggered):**
```
First child:  delay 100ms
Each next:    delay += 100ms
Duration:     500-600ms
Easing:       easeOut
Animation:    fade-in + slide-up
```

#### Keyframe Animations

**Float:**
```css
0%, 100% { transform: translateY(0px); }
50% { transform: translateY(-10px); }
Duration: 6s
Timing: ease-in-out
Repeat: infinite
```

**Pulse (Slow):**
```css
0%, 100% { opacity: 1; }
50% { opacity: 0.5; }
Duration: 3s
Timing: cubic-bezier(0.4, 0, 0.6, 1)
Repeat: infinite
```

**Glow Pulse:**
```css
0%, 100% { box-shadow: 0 0 20px rgba(32, 178, 170, 0.3); }
50% { box-shadow: 0 0 40px rgba(32, 178, 170, 0.6); }
Duration: 2s
Timing: ease-in-out
Repeat: infinite
```

**Wave Animation:**
```css
0% { transform: translateX(-100%); }
100% { transform: translateX(100%); }
Duration: 8-15s (varies by layer)
Timing: linear
Repeat: infinite
```

### Interactive States

#### Hover
```css
scale: 1.02-1.05 (depends on component)
opacity: 0.9-1 (slight change)
shadow: increase by 1 level
duration: 0.3s
```

#### Active (Tap/Click)
```css
scale: 0.95-0.98
duration: 0.15s
```

#### Focus (Keyboard)
```css
ring: 2px solid #20B2AA
ring-offset: 2px
outline: none
```

#### Disabled
```css
opacity: 0.5
cursor: not-allowed
pointer-events: none
```

### Responsive Design

#### Breakpoints
```
Mobile:  < 640px
Tablet:  640px - 1024px
Desktop: > 1024px
```

#### Mobile-First Adjustments
```
Font Sizes:
  h1: 32px → 48px (mobile → tablet)
  p:  14px → 16px (mobile → tablet)

Padding:
  Cards: 20px → 32px
  Forms: 16px → 24px
  
Spacing:
  Gap: 16px → 24px
  Margin: 12px → 24px

Touch Targets: 44px × 44px minimum
```

#### Desktop Optimizations
```
Hero Height: 100vh
Feature Cards: 3-column grid
Form Width: max-width 512px
Animations: Full effects enabled
```

### Accessibility Guidelines

#### Color Contrast
```
Foreground/Background Contrast Ratio: ≥ 4.5:1
- Text on Navy (#1A2B3C): White (#FFFFFF) ✓ 8.6:1
- Text on Navy: Teal (#20B2AA) ✓ 4.5:1
- Text on White: Navy (#1A2B3C) ✓ 8.6:1
```

#### Focus Management
```
Focus Order: Natural tab order (left-to-right, top-to-bottom)
Focus Indicator: 2px teal ring with 2px offset
Focus Trap: Enforce in modals
```

#### ARIA Attributes
```
Forms:
  label[for="id"] → input[id="id"]
  aria-invalid="true" (invalid fields)
  aria-describedby="error-id" (error messages)

Buttons:
  aria-label (for icon-only buttons)
  aria-haspopup="dialog" (trigger buttons)

Modals:
  role="dialog"
  aria-modal="true"
  aria-labelledby="title-id"
```

### Browser Support

#### CSS Features Used
- `backdrop-filter`: Chrome 76+, Safari 9+, Edge 79+
- `linear-gradient`: All modern browsers
- CSS Grid: All modern browsers
- CSS Flexbox: All modern browsers
- CSS Variables: All modern browsers

#### Fallbacks
```css
/* Fallback for backdrop-filter */
background: rgba(255, 255, 255, 0.1);
@supports (backdrop-filter: blur(10px)) {
  backdrop-filter: blur(10px);
}
```

### Performance Specifications

#### Animation Performance
- Use GPU-accelerated properties: `transform`, `opacity`
- Avoid animating: `width`, `height`, `left`, `top`
- Frame rate: Target 60fps
- Prefer CSS animations over JavaScript for simple effects

#### Loading Performance
- Font subset: Latin only (for now)
- Font system: System fonts as fallback
- Animation preload: Load on demand
- Image optimization: Use next/image component

### Dark Mode (Future)

**Dark Mode Color Overrides:**
```css
@media (prefers-color-scheme: dark) {
  /* Already optimized for dark */
}

@media (prefers-color-scheme: light) {
  --bg-navy: #F8F9FA;
  --text-primary: #1A2B3C;
  --text-secondary: #4B5563;
}
```

## Implementation Checklists

### Component Implementation
- [ ] Color palette correctly applied
- [ ] Typography hierarchy followed
- [ ] Spacing consistent with base unit
- [ ] Animations use specified timings
- [ ] Interactive states implemented
- [ ] Responsive breakpoints applied
- [ ] ARIA attributes added
- [ ] Touch targets ≥ 44px

### Testing Before Deploy
- [ ] Visual regression tests
- [ ] Responsive design testing (mobile, tablet, desktop)
- [ ] Animation performance (60fps maintained)
- [ ] Keyboard navigation works
- [ ] Screen reader tested
- [ ] Color contrast verified
- [ ] Touch interaction tested on real device
- [ ] Browser support verified

### Documentation
- [ ] Component Figma designs match code
- [ ] CSS classes documented
- [ ] Animation timings documented
- [ ] Color values consistent
- [ ] Accessibility notes included
