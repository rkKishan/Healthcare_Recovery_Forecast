# Frontend Deployment Guide

## Local Development

### Quick Start (5 minutes)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:3000

# Demo login: any hospital ID + any password (mock auth)
```

### With Backend Integration

See `INTEGRATION_GUIDE.md` for complete backend setup.

```bash
# Terminal 1: Backend
python api_server.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Or use Docker Compose for everything:

```bash
docker-compose up
```

## Build for Production

```bash
cd frontend
npm run build
npm start
```

## Docker Deployment

### Build Image
```bash
docker build -t hrf-frontend:latest -f frontend/Dockerfile .
```

### Run Container
```bash
docker run \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=http://backend:8000 \
  -e NODE_ENV=production \
  hrf-frontend:latest
```

## Deployment Platforms

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel deploy --prod

# Set environment variables in Vercel dashboard:
NEXT_PUBLIC_API_BASE_URL = https://api.yourdomain.com
```

### AWS Amplify

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Configure
amplify configure

# Deploy
cd frontend
amplify init
amplify publish
```

### Heroku

```bash
# Install Heroku CLI
brew install heroku

# Login
heroku login

# Create app
heroku create your-app-name

# Set buildpacks
heroku buildpacks:add heroku/nodejs

# Deploy
git push heroku main
```

### Azure App Service

```bash
# Install Azure CLI
brew install azure-cli

# Login
az login

# Deploy
az webapp create --resource-group myResourceGroup --plan myServicePlan --name myapp
```

## Environment Variables

### Development
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=development
DEBUG=true
```

### Production
```env
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NODE_ENV=production
DEBUG=false
ANALYTICS_ENABLED=true
```

## Performance Optimization

### Image Compression
```bash
cd public
# Compress images to WebP format
cwebp image.jpg -o image.webp
```

### Build Analysis
```bash
npm install --save-dev @next/bundle-analyzer

# In next.config.js:
// const withBundleAnalyzer = require('@next/bundle-analyzer')({
//   enabled: process.env.ANALYZE === 'true',
// })
// module.exports = withBundleAnalyzer(nextConfig)

ANALYZE=true npm run build
```

## Monitoring & Logging

### Application Error Tracking
Consider adding:
- **Sentry** - Error tracking
- **LogRocket** - Session replay
- **Datadog** - APM & monitoring

```javascript
// Add to app/layout.tsx
import * as Sentry from "@sentry/nextjs"

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
})
```

## Security Checklist

- [ ] HTTPS enabled for all endpoints
- [ ] CORS properly configured
- [ ] API authentication implemented (JWT)
- [ ] Input validation on all forms
- [ ] Environment variables secured
- [ ] API rate limiting enabled
- [ ] Security headers configured
- [ ] CSRF protection enabled
- [ ] XSS prevention implemented
- [ ] Secrets not committed to git

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    
    - uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - run: cd frontend && npm install
    - run: cd frontend && npm run lint
    - run: cd frontend && npm run build
    
    - name: Deploy to Vercel
      uses: vercel/action@master
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## Troubleshooting Deployment

### "Port already in use"
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### "Module not found"
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### "Environment variable not set"
- Verify `.env.local` exists
- Check env var names (must start with `NEXT_PUBLIC_` for client-side)
- Restart dev server after changing env vars

### "API CORS errors"
- Verify backend CORS headers
- Check `NEXT_PUBLIC_API_BASE_URL` matches backend origin
- Test with `curl:
```bash
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/api/predict/batch
```

## Rollback Procedure

### If deployed to Vercel
```bash
# View deployments
vercel list

# Rollback to previous
vercel rollback your-project-name --yes
```

### If using git
```bash
# Revert to previous commit
git revert HEAD
git push
```

## Monitoring Checklist

- [ ] Uptime monitoring (Pingdom, UptimeRobot)
- [ ] Error tracking (Sentry)
- [ ] Analytics (Google Analytics, Mixpanel)
- [ ] Performance monitoring (Vercel Analytics, Datadog)
- [ ] User feedback (Feedback widget)
- [ ] Backend API health checks

## Support & Documentation

- **Frontend README**: `frontend/README.md`
- **Setup Guide**: `frontend/SETUP_GUIDE.md`
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **Project README**: `README.md`

## Next Steps

1. ✅ Frontend application built and ready
2. **Deploy to staging** - Test with staging backend
3. **Setup production database** - Configure with real data
4. **Launch monitoring** - Setup error tracking and analytics
5. **User training** - Create documentation for hospital staff
6. **Collect feedback** - Iterate based on user input
