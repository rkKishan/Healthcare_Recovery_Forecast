# Glassmorphic Healthcare Dashboard - Setup & Configuration Guide

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

**Demo Login:**
- Hospital ID: `demo`
- Password: `any`

## Configuration

### Environment Variables

Create a `.env.local` file in the `/frontend` directory:

```env
# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# App name
NEXT_PUBLIC_APP_NAME=Healthcare Recovery Forecast
```

### Backend Integration

Update endpoints in `lib/api.ts` to match your FastAPI/Flask backend:

```python
# Python backend should provide:
POST   /api/upload           # Upload CSV/Excel
POST   /api/predict/batch    # Batch predictions
POST   /api/predict/single   # Single patient
GET    /api/predict/explain/:id  # SHAP explanations
GET    /api/dashboard/bed-occupancy
GET    /api/dashboard/severity
POST   /api/reports/generate
```

## Component Documentation

### Pages

#### Dashboard (`app/dashboard.tsx`)
- Main application layout
- Sidebar navigation
- Hospital statistics cards
- Bed occupancy heatmap
- Severity distribution donut
- Patient overview cards
- Patient detail sidebar

**Features:**
- Click patient cards to view detailed predictive summary
- Real-time metric updates
- Severity-based color coding (Level 1-5)
- Expected discharge dates with confidence intervals

#### Login (`components/Auth.tsx`)
- Glassmorphic authentication form
- Animated background with data nodes
- Mock authentication (replace with JWT in production)
- Error handling and loading states

#### Data Upload (`components/DataUpload.tsx`)
- Drag-and-drop file zone
- CSV/Excel file support
- Animated progress bar
- Upload success feedback

#### Analysis Dashboard (`components/Analysis.tsx`)
- Recovery timeline (Gantt-style)
- Feature importance bar chart
- Patient timeline events
- Recovery milestone tracking

#### Reports (`components/Reports.tsx`)
- PDF report generation
- Print-optimized light background
- Hospital header with logo placeholder
- Summary statistics table
- Chart snapshots in PDF
- Predicted discharge dates

### Reusable Components

#### UI Base Components (`components/ui.tsx`)

**AnimatedBackground**
```jsx
<AnimatedBackground />
// Creates floating data nodes with animation
```

**GlassmorphicCard**
```jsx
<GlassmorphicCard delay={0.2} className="...">
  <div>Content</div>
</GlassmorphicCard>
// Soft glass effect with hover animation
```

**Badge**
```jsx
<Badge level={3} text="Moderate" />
// Color-coded severity indicator
```

**LoadingSpinner**
```jsx
<LoadingSpinner size="md" />
// Animated spinner with Tailwind
```

#### Dashboard Components (`components/Dashboard.tsx`)

**BedGrid**
- 14-day occupancy heatmap
- Color intensity based on utilization
- Hover interactions

```jsx
<BedGrid data={bedOccupancyData} />
```

**SeverityDonut**
- Animated donut chart
- Severity distribution (1-5)
- Legend with percentages

```jsx
<SeverityDonut data={severityDistribution} />
```

#### Analysis Components (`components/Analysis.tsx`)

**RecoveryTimeline**
- Gantt-style patient recovery visualization
- Event status indicators (completed, ongoing, planned)
- Timeline with milestones

**FeatureImportance**
- Horizontal bar chart
- Positive/negative impact indicators
- Animated bar growth

```jsx
<FeatureImportance features={importanceData} />
```

#### Report Components (`components/Reports.tsx`)

**PDFReportGeneratorButton**
- Generates print-optimized PDFs
- Includes charts and statistics
- Auto-download with timestamp

**PatientReportCard**
- Patient summary card
- Key metrics (LOS, confidence, discharge date)
- Severity badge
- Contributing factors

```jsx
<PatientReportCard 
  patientId="001"
  name="John Doe"
  severity={3}
  predictedLOS={7}
  confidence={92}
  dischargeDate="2026-04-05"
  factors={['Age 65+', 'HTN', 'Abnormal vitals']}
/>
```

## Design System

### Colors
- **Primary**: Deep Navy `#1A2B3C`
- **Accent**: Soft Teal `#20B2AA`
- **Background**: Gradient from Navy to Blue
- **Surface**: Semi-transparent white with blur

### Severity Color Coding
- **Level 1**: Green `#10B981` (Minimal)
- **Level 2**: Amber `#F59E0B` (Mild)
- **Level 3**: Orange `#F97316` (Moderate)
- **Level 4**: Red `#EF4444` (Severe)
- **Level 5**: Purple `#7C3AED` (Critical)

### Animations
- Entrance animations: Fade + slide (0.5s)
- Hover effects: Scale (0.3s) + color transition
- Loading: Rotating spinner or pulse
- Background: Floating nodes with soft animation

### Glass Morphism
- Backdrop filter: `blur(10px)`
- Background: `rgba(255,255,255, 0.1)`
- Border: `1px solid rgba(255,255,255, 0.2)`
- Shadow: `0 8px 32px 0 rgba(31, 38, 135, 0.37)`

## State Management (Zustand)

### Auth Store
```javascript
const {
  user,              // Current user object
  isAuthenticated,   // Auth status
  isLoading,        // Loading indicator
  login,            // Login function
  logout,           // Logout function
  setUser,          // Set user directly
} = useAuthStore()
```

### Data Store
```javascript
const {
  uploadedData,     // Uploaded patient dataset
  predictions,      // Model predictions
  selectedSeverity, // Filter by severity
  selectedWard,     // Filter by ward
  setUploadedData,
  setPredictions,
  setFilters,
} = useDataStore()
```

## API Integration

### Using the API Client

```javascript
import { api } from '@/lib/api'

// Upload file
const response = await api.upload.file(file, hospitalId)

// Get predictions
const predictions = await api.predictions.analyze(patientData)

// Get SHAP explanations
const explanation = await api.predictions.explain(patientId)

// Generate PDF report
const pdf = await api.reports.generate(reportData)
```

## Running with Docker

### Build Image
```bash
docker build -t hrf-frontend:latest .
```

### Run Container
```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=http://backend:8000 \
  hrf-frontend:latest
```

## Customization Guide

### Change Theme Colors

Edit `tailwind.config.ts`:

```typescript
colors: {
  'navy': '#YOUR_NAVY',
  'teal': '#YOUR_TEAL',
  // ... other colors
}
```

### Add New Pages

Create new folder in `app/`:

```
app/
├── settings/
│   └── page.tsx    (Settings page)
├── reports/
│   └── page.tsx    (Historical reports)
``` 

Update sidebar navigation in `app/dashboard.tsx`.

### Customize Animations

Edit animation duration in `lib/constants.ts`:

```javascript
export const ANIMATION_DURATION = {
  fast: 150,      // Adjust as needed
  normal: 300,
  slow: 500,
}
```

## Troubleshooting

### Dashboard not loading?
- Check `NEXT_PUBLIC_API_BASE_URL` environment variable
- Verify backend is running at the correct URL
- Check browser console for CORS errors

### Predictions showing as null?
- Ensure Python backend is training and saving models
- Verify models are in `../ml/` directory (accessible to backend)
- Check API endpoint in `lib/api.ts` matches backend routes

### PDF generation not working?
- Verify `html2canvas` and `jspdf` are installed
- Check browser console for canvas rendering errors
- Charts may need to be rendered before PDF generation

### Animations not smooth?
- Check device GPU support for hardware acceleration
- Reduce animation time in constants
- Disable animations for older browsers

## Production Deployment

### Build for Production
```bash
npm run build
npm start
```

### Environment Setup
```bash
# Production environment variables
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
```

### Security Considerations
- [ ] Replace mock authentication with JWT
- [ ] Add CORS configuration for backend
- [ ] Implement API rate limiting
- [ ] Add input validation for all forms
- [ ] Use HTTPS for all connections
- [ ] Secure sensitive data in localStorage

## Performance Optimization

### Already Implemented
- ✅ Image optimization with Next.js
- ✅ Code splitting by route
- ✅ Component lazy loading with Suspense
- ✅ Zustand for efficient state management
- ✅ Memoization of expensive components

### Additional Optimization Opportunities
- Add progressive image loading
- Implement virtual scrolling for large tables
- Cache API responses with SWR or TanStack Query
- Minify and compress assets
- Use CDN for static content

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Minimum support for backdrop-filter CSS and ES2020 JavaScript.
