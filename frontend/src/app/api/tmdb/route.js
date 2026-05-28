import { NextResponse } from 'next/server';

export async function GET(request) {
    const { searchParams } = new URL(request.url);
    const movieId = searchParams.get('movie_id');
    
    if (!movieId || !/^\d+$/.test(movieId)) {
        return NextResponse.json({ error: 'Invalid movie ID' }, { status: 400 });
    }

    const apiKey = process.env.NEXT_PUBLIC_TMDB_API_KEY;
    if (!apiKey) {
        return NextResponse.json({ error: 'TMDB configuration missing' }, { status: 500 });
    }

    try {
        const lang = searchParams.get('language') || 'en,null';
        const url = `https://api.themoviedb.org/3/movie/${movieId}/images?api_key=${apiKey}&include_image_language=${encodeURIComponent(lang)}`;
        
        const response = await fetch(url, { 
            cache: 'force-cache',
            next: { revalidate: 86400 } // Cache for 24 hours
        });

        if (!response.ok) {
            return NextResponse.json({ error: 'TMDB request failed' }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        if (process.env.NODE_ENV === 'development') console.error('TMDB proxy error:', error);
        return NextResponse.json({ error: 'Failed to fetch from TMDB' }, { status: 500 });
    }
}
