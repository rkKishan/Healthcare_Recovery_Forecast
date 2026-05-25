// Next.js API routes for proxying backend calls
// This file sets up API routes that forward requests to the Python backend

import { NextRequest, NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/')
  
  try {
    const body = await req.json()
    
    const response = await fetch(`${API_BASE_URL}/api/${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: req.headers.get('Authorization') || '',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/')
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: req.headers.get('Authorization') || '',
      },
    })

    const data = await response.json()
    
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
