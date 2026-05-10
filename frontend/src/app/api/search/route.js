import { NextResponse } from 'next/server';

export async function GET(request) {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');
    const k = searchParams.get('k') || '25';
    
    // Get secrets from environment (these are safe on the server!)
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    const hfToken = process.env.NEXT_PUBLIC_HF_TOKEN;

    if (!backendUrl || !hfToken) {
        return NextResponse.json({ error: 'Backend configuration missing' }, { status: 500 });
    }

    try {
        const url = `${backendUrl}/search?q=${encodeURIComponent(query)}&k=${k}`;
        console.log("📡 Proxying request to:", url);

        const response = await fetch(url, {
            headers: {
                "Authorization": `Bearer ${hfToken}`
            }
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
