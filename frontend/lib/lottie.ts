// Lottie animations configuration
// Add animated loading states throughout the application

export const loadingAnimation = {
  // Success animation (checkmark)
  success: {
    loop: false,
    autoplay: true,
    animationData: {
      // Animation JSON from lottie files
      // Can be imported from public/animations/success.json
    },
  },
  
  // Loading spinner animation
  loading: {
    loop: true,
    autoplay: true,
    animationData: {
      // Animation JSON from public/animations/loading.json
    },
  },

  // Error animation
  error: {
    loop: false,
    autoplay: true,
    animationData: {
      // Animation JSON from public/animations/error.json
    },
  },

  // Data processing animation
  processing: {
    loop: true,
    autoplay: true,
    animationData: {
      // Animation JSON from public/animations/processing.json
    },
  },
}

// Example usage in component:
/*
import Lottie from 'lottie-react'
import { loadingAnimation } from '@/lib/lottie'

export const ProcessingState = () => (
  <Lottie
    animationData={loadingAnimation.processing.animationData}
    loop={true}
    autoplay={true}
    style={{ width: 200, height: 200 }}
  />
)
*/
