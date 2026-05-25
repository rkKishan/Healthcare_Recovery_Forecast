# Healthcare Recovery Forecast - Frontend

A modern, responsive React/Next.js dashboard for healthcare analytics with predictions, visualizations, and PDF reports.

## Features

### 🎨 Visual Identity
- **Clinical Modernist** theme with Deep Navy (#1A2B3C) and Soft Teal (#20B2AA)
- Glassmorphic UI components for a premium, cutting-edge feel
- Subtle micro-interactions and smooth animations
- Dark mode optimized for healthcare environments

### 📊 Dashboard Pages

#### 1. **Login/Auth Page**
- Centered glassmorphic login card
- Animated background with abstract data nodes
- Mock authentication for demo purposes
- Hospital ID + Password fields

#### 2. **Main Dashboard (Hospital View)**
- **Bed Grid Heatmap**: 14-day predicted vs. current occupancy forecast
- **Severity Distribution Donut**: Breakdown of patients in Levels 1-5
- **Key Metrics Cards**: Overall statistics and trend indicators
- **Current Patients Overview**: Quick view of critical cases

#### 3. **Data Upload Hub**
- Drag & drop file upload zone
- Support for CSV and Excel files
- Animated progress bar during processing
- Real-time dataset import

#### 4. **Analysis Dashboard (Patient View)**
- **Recovery Timeline**: Gantt-style patient recovery paths
- **Feature Importance**: Bar chart showing recovery factors
- **Patient Reports**: Individual predictions with confidence intervals

### 🛠️ Technical Stack

- **Framework**: Next.js 14 with App Router
- **UI Library**: React 18 with Framer Motion
- **Styling**: Tailwind CSS with custom glassmorphic components
- **State Management**: Zustand
- **Charts**: Recharts for visualizations
- **PDF Generation**: jsPDF + html2canvas
- **File Upload**: react-dropzone
- **Animations**: Lottie (ready for integration)
- **API Client**: Axios with interceptors

### 📦 Installation

```bash
cd frontend
npm install
```

### 🚀 Development

```bash
npm run dev
```

Visit `http://localhost:3000`

### 🏗️ Build

```bash
npm run build
npm start
```

### 📁 Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── api/               # API routes (proxy to backend)
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── dashboard.tsx      # Main dashboard
├── components/            # React components
│   ├── ui.tsx            # Base UI components
│   ├── Auth.tsx          # Authentication
│   ├── Dashboard.tsx     # Dashboard charts
│   ├── Analysis.tsx      # Analysis visualizations
│   ├── DataUpload.tsx    # File upload
│   └── Reports.tsx       # PDF reports
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   ├── store.ts          # Zustand stores
│   ├── constants.ts      # Theme & constants
├── styles/               # Global styles
│   └── globals.css       # Tailwind + custom CSS
├── public/               # Static assets
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── tailwind.config.ts    # Tailwind configuration
└── next.config.js        # Next.js configuration
```

### 🔌 Backend Integration

The frontend communicates with a FastAPI/Flask backend at `/api/*` endpoints:

```javascript
// Example: Upload dataset
POST /api/upload
- file: File
- hospital_id: string

// Example: Get predictions
POST /api/predict/batch
- patients: Array<PatientData>

// Example: Generate bed forecast
GET /api/dashboard/bed-occupancy
```

### 🎬 Key Components

#### `GlassmorphicCard`
Premium card component with backdrop blur and hover effects.

```jsx
<GlassmorphicCard>
  <div>Your content here</div>
</GlassmorphicCard>
```

#### `BedGrid`
14-day occupancy heatmap with color intensity based on utilization.

```jsx
<BedGrid data={bedData} />
```

#### `SeverityDonut`
Donut chart showing distribution of patients across severity levels.

```jsx
<SeverityDonut data={severityData} />
```

#### `PDFReportGeneratorButton`
Generate and download print-optimized PDF reports.

```jsx
<PDFReportGeneratorButton 
  data={reportData}
  isLoading={isGenerating}
/>
```

### 📊 State Management

Using Zustand for lightweight, scalable state:

```javascript
// Authentication store
const { user, isAuthenticated, login, logout } = useAuthStore()

// Data store
const { uploadedData, predictions, setFilters } = useDataStore()
```

### 🎨 Customization

#### Theme Colors
Edit `tailwind.config.ts`:

```javascript
colors: {
  'navy': '#1A2B3C',      // Primary
  'teal': '#20B2AA',      // Accent
  'white': '#FFFFFF',
}
```

#### Animations
All components use Framer Motion for smooth transitions:

```jsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.5 }}
>
  Animated content
</motion.div>
```

### 🔒 Authentication

Currently uses mock authentication. To integrate with backend:

1. Update `lib/store.ts` - `login()` method
2. Store JWT token in localStorage
3. API interceptor automatically adds token to requests

### 📝 Next Steps

- [ ] Integrate with Python ML backend
- [ ] Implement Lottie animations for loading states
- [ ] Add real chart data from API
- [ ] Complete Analysis Dashboard page
- [ ] Add patient filtering and search
- [ ] Implement real-time WebSocket updates
- [ ] Add export to Excel functionality
- [ ] Setup Docker containerization

### 📧 Requirements

See `../requirements.txt` for Python dependencies.

Frontend dependencies are managed via `package.json`.

### 📄 License

Part of Healthcare Recovery Forecast system.
