import { NextResponse } from 'next/server';

export async function GET(request) {
    const { searchParams } = new URL(request.url);
    
    // Get secrets from environment
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    const hfToken = process.env.NEXT_PUBLIC_HF_TOKEN;

    if (!backendUrl || !hfToken) {
        return NextResponse.json({ error: 'Backend configuration missing' }, { status: 500 });
    }

    try {
        // Forward all query parameters to the backend
        const url = `${backendUrl}/search?${searchParams.toString()}`;
        console.log("📡 Proxying request to:", url);

        // Build headers — include user's JWT if provided for personalization
        const headers = {
            "Authorization": `Bearer ${hfToken}`
        };

        // Forward user's auth token for taste-based personalization
        const userToken = request.headers.get('x-user-token');
        if (userToken) {
            headers["Authorization"] = `Bearer ${userToken}`;
        }

        const response = await fetch(url, {
            cache: 'no-store',
            headers
        });

        if (!response.ok) {
            const errorText = await response.text();
            return NextResponse.json({ error: errorText }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("🚨 Proxy Error:", error);
        return NextResponse.json({ error: 'Failed to connect to backend' }, { status: 500 });
    }
}
