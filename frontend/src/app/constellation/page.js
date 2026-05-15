"use client";

import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Keyboard, MousePointer2 } from 'lucide-react';
import * as THREE from 'three';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { 
    ssr: false,
    loading: () => (
        <div className="flex h-screen w-full items-center justify-center bg-black text-[#ff0055]">
            <Loader2 className="h-12 w-12 animate-spin mb-4" />
        </div>
    )
});

export default function ConstellationPage() {
    const fgRef = useRef();
    const lastHoverId = useRef(null);
    const hoverTimer = useRef(null);
    const frameCount = useRef(0);
    const [data, setData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [selectedNode, setSelectedNode] = useState(null);
    const [hoverNode, setHoverNode] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedDetails, setSelectedDetails] = useState(null);
    const [hoveredDetails, setHoveredDetails] = useState(null);
    const [currentSector, setCurrentSector] = useState('DEEP SPACE');
    const [neighborIds, setNeighborIds] = useState(new Set());
    const [isLocked, setIsLocked] = useState(false);
    const [exploration, setExploration] = useState(0);

    const sectorAnchors = useMemo(() => [
        { name: 'HORROR', search: 'Scream' },
        { name: 'ROMANCE', search: 'Titanic' },
        { name: 'SCI-FI', search: 'Interstellar' },
        { name: 'ACTION', search: 'Mad Max' },
        { name: 'DRAMA', search: 'Godfather' }
    ], []);

    const [anchorsWithCoords, setAnchorsWithCoords] = useState([]);

    const loadGalaxy = useCallback(async () => {
        try {
            let points;
            try {
                const res = await fetch('/galaxy_points.json');
                if (!res.ok) throw new Error("Public file missing");
                points = await res.json();
            } catch (e) {
                console.log("FALLBACK: Fetching from backend API...");
                const res = await fetch('http://localhost:8000/api/v1/constellation/points');
                points = await res.json();
            }

            if (!points || !Array.isArray(points)) {
                console.error("CRITICAL: Signal data is invalid or empty.");
                setLoading(false);
                return;
            }

            const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
            
            console.log(`SYNC: Processing ${points.length} neural points...`);
            
            let favorites = [];
            try {
                const authRes = await fetch('http://localhost:8000/api/v1/sbtxt-auth/bundle', { headers });
                const authData = await authRes.json();
                favorites = authData.profile?.favorites || [];
            } catch(e) {}

            let watchedHistory = [];
            try {
                const watchRes = await fetch('http://localhost:8000/api/v1/sbtxt-sync/library?type=watched', { headers });
                const watchData = await watchRes.json();
                watchedHistory = watchData.movies || [];
            } catch(e) {}

            const favIds = new Set(favorites.map(f => String(f.tmdb_id || f.id)));
            const watchedIdsSet = new Set(watchedHistory.map(m => String(m.tmdb_id)));
            const recentIds = new Set(watchedHistory.slice(0, 4).map(m => String(m.tmdb_id)));

            const nodes = points.map(p => {
                const id = String(p.i);
                let type = 'neutral';
                if (watchedIdsSet.has(id)) type = 'watched';
                if (recentIds.has(id)) type = 'recent';
                if (favIds.has(id)) type = 'favorite';
                const x = p.x * 500; const y = p.y * 500; const z = p.z * 500;
                return { id, name: p.t, x, y, z, fx: x, fy: y, fz: z, type };
            });

            const explored = (watchedIdsSet.size / (nodes.length || 1)) * 100;
            setExploration(explored);

            const links = [];
            const favNodes = nodes.filter(n => n.type === 'favorite');
            for (let i = 0; i < favNodes.length - 1; i++) {
                links.push({ source: favNodes[i].id, target: favNodes[i+1].id, type: 'favorite' });
            }
            const recentNodes = nodes.filter(n => n.type === 'recent');
            for (let i = 0; i < recentNodes.length - 1; i++) {
                links.push({ source: recentNodes[i].id, target: recentNodes[i+1].id, type: 'recent' });
            }

            const resolvedAnchors = sectorAnchors.map(a => {
                const m = nodes.find(n => n.name.toLowerCase().includes(a.search.toLowerCase()));
                return m ? { ...a, x: m.x, y: m.y, z: m.z } : null;
            }).filter(Boolean);
            setAnchorsWithCoords(resolvedAnchors);

            const sum = nodes.reduce((acc, n) => ({ x: acc.x + n.x, y: acc.y + n.y, z: acc.z + n.z }), { x: 0, y: 0, z: 0 });
            const centroid = { x: sum.x / (nodes.length || 1), y: sum.y / (nodes.length || 1), z: sum.z / (nodes.length || 1) };

            setData({ nodes, links, centroid });
            setLoading(false);

            setTimeout(() => {
                const target = favNodes[0] || centroid;
                if (fgRef.current && target) {
                    fgRef.current.cameraPosition({ x: target.x, y: target.y, z: target.z + 800 }, target, 3000);
                }
            }, 1000);
        } catch (error) {
            console.error("GALAXY_LOAD_ERROR:", error);
            setLoading(false);
        }
    }, [sectorAnchors]);

    useEffect(() => {
        loadGalaxy();
    }, [loadGalaxy]);

    useEffect(() => {
        const interval = setInterval(() => {
            if (!fgRef.current || anchorsWithCoords.length === 0) return;
            const camera = fgRef.current.camera();
            if (!camera) return;
            let nearest = null;
            let minDist = Infinity;
            anchorsWithCoords.forEach(a => {
                const d = Math.hypot(camera.position.x - a.x, camera.position.y - a.y, camera.position.z - a.z);
                if (d < minDist) { minDist = d; nearest = a; }
            });
            if (nearest && minDist < 4000) setCurrentSector(nearest.name);
            else setCurrentSector('DEEP SPACE');
        }, 1000);
        return () => clearInterval(interval);
    }, [anchorsWithCoords]);

    const highlightMovie = useCallback(async (node) => {
        // SIGNAL ANCHOR: If clicking what's already selected, do nothing.
        if (node?.id === selectedNode?.id) return;

        // INSTANT PURGE: Only purge if we are actually changing state
        if (hoverTimer.current) clearTimeout(hoverTimer.current);
        setHoverNode(null);
        setHoveredDetails(null);
        lastHoverId.current = null;

        if (!node) {
            if (!selectedNode) return; // Already in void state
            setSelectedNode(null);
            setSelectedDetails(null);
            setNeighborIds(new Set());
            return;
        }
        setSelectedDetails(null);
        setSelectedNode(node);
        setSearchResults([]);
        setSearchQuery('');
        const others = data.nodes.filter(n => n.id !== node.id);
        const neighbors = others
            .map(n => ({ id: n.id, dist: Math.hypot(n.x - node.x, n.y - node.y, n.z - node.z) }))
            .sort((a, b) => a.dist - b.dist)
            .slice(0, 5);
        setNeighborIds(new Set(neighbors.map(n => n.id)));
        try {
            const res = await fetch(`http://localhost:8000/movies/${node.id}`);
            const details = await res.json();
            setSelectedDetails(details);
        } catch (e) {}
    }, [data.nodes, selectedNode]);

    const handleNodeHover = useCallback(async (node) => {
        const isNeighbor = node && neighborIds.has(node.id);
        if (!node || !isNeighbor) { 
            if (hoverTimer.current) clearTimeout(hoverTimer.current);
            
            // NEURAL SNAP-BACK: If we have a selection, return to it instantly.
            // If in void, use hysteresis to prevent flickering.
            if (selectedNode) {
                setHoverNode(null); 
                setHoveredDetails(null); 
                lastHoverId.current = null;
            } else {
                hoverTimer.current = setTimeout(() => {
                    setHoverNode(null); 
                    setHoveredDetails(null); 
                    lastHoverId.current = null;
                }, 500);
            }
            return; 
        }
        
        if (hoverTimer.current) clearTimeout(hoverTimer.current);
        
        if (!hoverNode || hoverNode.id !== node.id) {
            setHoveredDetails(null);
            setHoverNode(node);
            lastHoverId.current = node.id;
            try {
                const res = await fetch(`http://localhost:8000/movies/${node.id}`);
                const details = await res.json();
                setHoveredDetails(details);
            } catch (e) {}
        }
    }, [neighborIds, hoverNode]);

    const getTargetFromCrosshair = useCallback((isHover = false) => {
        if (!fgRef.current || !data.nodes.length) return null;
        const camera = fgRef.current.camera();
        const camPos = camera.position;
        const vector = new THREE.Vector3();
        
        let bestNode = null;
        let minDepth = Infinity;
        const baseRadius = 0.15 * 50; 

        for (let i = 0; i < data.nodes.length; i++) {
            const node = data.nodes[i];
            const worldDist = Math.hypot(node.x - camPos.x, node.y - camPos.y, node.z - camPos.z);
            const isNeighbor = neighborIds.has(node.id);
            const isSeen = node.type !== 'neutral';
            const rangeCap = (isNeighbor || isSeen) ? 5000 : 500;
            if (worldDist > rangeCap) continue; 

            vector.set(node.x, node.y, node.z);
            vector.project(camera);
            if (vector.z < 0 || vector.z > 1) continue;

            const screenDist = Math.hypot(vector.x, vector.y);

            // NEURAL DISCIPLINE: During hover (scouting), ignore undiscovered stars.
            // But if isHover is false (Clicking), we allow undiscovered selection.
            if (isHover) {
                const isNeighborNode = neighborIds.has(node.id);
                const isPersonal = node.type !== 'neutral';
                if (!isNeighborNode && !isPersonal) continue;
            }

            // SURFACE-AWARE: We use a tuned baseRadius (2.0) to match the visual dot size.
            // This ensures you can hover anywhere on the star's surface when up close.
            const baseRadiusFixed = 2.0; 
            const projectedRadius = baseRadiusFixed / worldDist; 
            
            const hitPadding = isHover ? 0.008 : 0.015; 
            const finalThreshold = Math.max(projectedRadius, hitPadding);

            if (screenDist < finalThreshold) {
                if (vector.z < minDepth) {
                    minDepth = vector.z;
                    bestNode = node;
                }
            }
        }
        return bestNode;
    }, [data.nodes, neighborIds]);

    const warpToMovie = useCallback((node) => {
        if (!node || !fgRef.current) return;
        highlightMovie(node);
        fgRef.current.cameraPosition({ x: node.x, y: node.y, z: node.z + 80 }, node, 2500);
    }, [highlightMovie]);

    const handleSearch = (q) => {
        setSearchQuery(q);
        if (q.length < 2) { setSearchResults([]); return; }
        const matches = data.nodes.filter(n => n.name.toLowerCase().includes(q.toLowerCase())).slice(0, 8);
        setSearchResults(matches);
    };

    useEffect(() => {
        const cruiseSpeed = 5;
        const sprintSpeed = 80;
        const keys = {};
        let euler = new THREE.Euler(0, 0, 0, 'YXZ');
        let animationFrame;

        const handleKeyDown = (e) => keys[e.code] = true;
        const handleKeyUp = (e) => keys[e.code] = false;
        const handleBlur = () => Object.keys(keys).forEach(k => keys[k] = false);
        const handleLockChange = () => setIsLocked(document.pointerLockElement === document.body);
        
        const handleMouseMove = (e) => {
            if (document.pointerLockElement === document.body && fgRef.current) {
                const camera = fgRef.current.camera();
                if (!camera) return;
                const sensitivity = 0.002;
                euler.setFromQuaternion(camera.quaternion);
                euler.y -= e.movementX * sensitivity;
                euler.x -= e.movementY * sensitivity;
                euler.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, euler.x));
                camera.quaternion.setFromEuler(euler);
                const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
                fgRef.current.controls().target.copy(camera.position).add(dir);
            }
        };

        const handleClick = (e) => {
            if (document.pointerLockElement === document.body) {
                if (e.button === 2) {
                    highlightMovie(null);
                } else {
                    // STEALTH DISCOVERY: Clicks have full spectrum visibility.
                    const clickTarget = getTargetFromCrosshair(false);
                    highlightMovie(clickTarget);
                }
            } else if (!searchQuery) {
                document.body.requestPointerLock();
            }
        };

        const handleContextMenu = (e) => {
            if (document.pointerLockElement === document.body) e.preventDefault();
        };

        const update = () => {
            if (fgRef.current) {
                const camera = fgRef.current.camera();
                const controls = fgRef.current.controls();
                const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
                const side = new THREE.Vector3().crossVectors(camera.up, dir).normalize();
                const up = new THREE.Vector3(0, 1, 0);
                const moveVec = new THREE.Vector3(0, 0, 0);
                const currentSpeed = (keys['ShiftLeft'] || keys['ShiftRight']) ? sprintSpeed : cruiseSpeed;
                
                if (keys['KeyW']) moveVec.addScaledVector(dir, currentSpeed);
                if (keys['KeyS']) moveVec.addScaledVector(dir, -currentSpeed);
                if (keys['KeyA']) moveVec.addScaledVector(side, currentSpeed);
                if (keys['KeyD']) moveVec.addScaledVector(side, -currentSpeed);
                if (keys['KeyQ']) moveVec.addScaledVector(up, currentSpeed);
                if (keys['KeyE']) moveVec.addScaledVector(up, -currentSpeed);
                
                if (moveVec.length() > 0) {
                    camera.position.add(moveVec);
                    controls.target.copy(camera.position).add(dir);
                    controls.update();
                }

                if (document.pointerLockElement === document.body) {
                    frameCount.current++;
                    if (frameCount.current % 2 === 0) {
                        const target = getTargetFromCrosshair(true);
                        handleNodeHover(target);
                    }
                }
            }
            animationFrame = requestAnimationFrame(update);
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        window.addEventListener('blur', handleBlur);
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mousedown', handleClick);
        window.addEventListener('contextmenu', handleContextMenu);
        document.addEventListener('pointerlockchange', handleLockChange);
        
        animationFrame = requestAnimationFrame(update);

        return () => {
            cancelAnimationFrame(animationFrame);
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
            window.removeEventListener('blur', handleBlur);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mousedown', handleClick);
            window.removeEventListener('contextmenu', handleContextMenu);
            document.removeEventListener('pointerlockchange', handleLockChange);
        };
    }, [searchQuery, data, highlightMovie, getTargetFromCrosshair, handleNodeHover]);

    return (
        <main className="relative h-screen w-full overflow-hidden bg-black font-mono">
            {/* REACTIVE CROSSHAIR */}
            {isLocked && (
                <div className="pointer-events-none absolute inset-0 z-[100] flex items-center justify-center transition-all duration-200">
                    <div className="relative">
                        <motion.div 
                            animate={{ 
                                borderColor: hoverNode ? (
                                    hoverNode.type === 'favorite' ? '#ff0055' :
                                    hoverNode.type === 'recent' ? '#bc13fe' :
                                    neighborIds.has(hoverNode.id) ? '#ffaa00' :
                                    hoverNode.type === 'watched' ? '#00ff88' : '#ffffff'
                                ) : 'rgba(255, 255, 255, 0.2)',
                                scale: hoverNode ? 1.2 : 1
                            }}
                            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                            className="h-6 w-6 border rounded-full" 
                        />
                        <motion.div 
                            animate={{ 
                                backgroundColor: hoverNode ? (
                                    hoverNode.type === 'favorite' ? '#ff0055' :
                                    hoverNode.type === 'recent' ? '#bc13fe' :
                                    neighborIds.has(hoverNode.id) ? '#ffaa00' :
                                    hoverNode.type === 'watched' ? '#00ff88' : '#ffffff'
                                ) : 'rgba(255, 255, 255, 0.4)'
                            }}
                            className="absolute top-1/2 left-1/2 h-[1px] w-3 -translate-x-1/2 -translate-y-1/2" 
                        />
                        <motion.div 
                            animate={{ 
                                backgroundColor: hoverNode ? (
                                    hoverNode.type === 'favorite' ? '#ff0055' :
                                    hoverNode.type === 'recent' ? '#bc13fe' :
                                    neighborIds.has(hoverNode.id) ? '#ffaa00' :
                                    hoverNode.type === 'watched' ? '#00ff88' : '#ffffff'
                                ) : 'rgba(255, 255, 255, 0.4)'
                            }}
                            className="absolute top-1/2 left-1/2 h-3 w-[1px] -translate-x-1/2 -translate-y-1/2" 
                        />
                    </div>
                </div>
            )}

            <div className="absolute top-8 left-8 z-50 flex flex-col gap-6 items-start text-white">
                <input 
                    type="text" placeholder="WARP TO MOVIE..." value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="w-48 bg-transparent border-b border-white/40 py-2 text-[10px] tracking-[0.4em] text-white outline-none placeholder:text-white/20 uppercase focus:border-[#ff0055] transition-all focus:w-80 font-bold"
                />
                
                <AnimatePresence>
                    {searchResults.length > 0 && (
                        <motion.div className="w-80 bg-black/95 backdrop-blur-3xl border border-white/20 shadow-2xl overflow-hidden font-bold">
                            {searchResults.map(m => (
                                <button key={m.id} onClick={() => warpToMovie(m)} className="w-full p-4 text-left text-[9px] tracking-widest text-white/60 hover:text-white hover:bg-[#ff0055]/20 uppercase transition-all flex justify-between items-center border-b border-white/5 last:border-0">
                                    <span>{m.name}</span>
                                    {m.type === 'favorite' && <span className="text-[#ff0055]">◈</span>}
                                </button>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>

                <AnimatePresence mode="wait">
                    {(selectedNode || (hoverNode && neighborIds.has(hoverNode.id))) && (
                        <motion.div key={(hoverNode || selectedNode).id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex gap-6 border border-white/10 bg-black/40 p-6 backdrop-blur-3xl shadow-2xl rounded-sm">
                            <div className="relative h-32 w-20 border border-white/10 bg-white/5 overflow-hidden flex items-center justify-center shrink-0">
                                {(hoveredDetails || selectedDetails) ? (
                                    <img src={`https://image.tmdb.org/t/p/w200${(hoveredDetails || selectedDetails).poster_path}`} className="h-full w-full object-cover shadow-2xl" />
                                ) : (
                                    <Loader2 className="h-6 w-6 animate-spin text-white/20" />
                                )}
                            </div>
                            <div className="flex flex-col justify-center text-left">
                                <p className={`text-[8px] tracking-[0.4em] uppercase font-black mb-2 ${
                                    (hoverNode || selectedNode).type === 'favorite' ? 'text-[#ff0055]' :
                                    ((hoverNode || selectedNode).type === 'recent' ? 'text-[#bc13fe]' :
                                    (neighborIds.has((hoverNode || selectedNode).id) ? 'text-[#ffaa00]' :
                                    ((hoverNode || selectedNode).type === 'watched' ? 'text-[#00ff88]' : 'text-white/60')))
                                }`}>
                                    {selectedNode && (hoverNode || selectedNode).id === selectedNode.id && <span className="text-[#00ffff] mr-2">◈ ACTIVE</span>}
                                    {(hoverNode || selectedNode).type === 'favorite' ? 'North Star' :
                                     ((hoverNode || selectedNode).type === 'recent' ? 'Neural Pulse' :
                                     (neighborIds.has((hoverNode || selectedNode).id) ? 'Similar Signal' :
                                     ((hoverNode || selectedNode).type === 'watched' ? 'Neural Log' : 'Undiscovered')))}
                                </p>
                                <h2 className="text-xl font-light tracking-tight text-white uppercase italic leading-tight max-w-[200px]">{(hoverNode || selectedNode).name}</h2>
                                <p className="text-[10px] tracking-[0.2em] text-white/40 uppercase font-bold mt-1">{((hoveredDetails || selectedDetails)?.release_date)?.split('-')[0] || 'Year Unknown'}</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="absolute top-8 right-8 z-50 text-right">
                <p className="text-[10px] tracking-[0.5em] text-white/30 uppercase font-black mb-1">Navigation System</p>
                <div className="flex items-center justify-end gap-3 mb-2">
                    <div className="h-[2px] w-8 bg-[#ff0055]" />
                    <p className="text-xl font-light tracking-[0.3em] text-white uppercase italic">{currentSector} SECTOR</p>
                </div>
                <p className="text-[9px] tracking-[0.4em] text-[#00ff88] uppercase font-bold tabular-nums">
                    Matrix Explored: {exploration.toFixed(5)}%
                </p>
                <p className="text-[7px] tracking-[0.3em] text-white/20 uppercase font-bold mt-1">
                    Universal Signals: 6,174,821 Entry Total
                </p>
            </div>

            <div className="absolute bottom-12 right-12 z-50 flex flex-col gap-2 p-6 bg-black/60 border border-white/10 backdrop-blur-3xl rounded-sm text-[9px] tracking-widest text-white/60 uppercase font-bold min-w-[200px]">
                <p className="text-[#ff0055] mb-2 font-black tracking-[0.3em]">Flight Controls</p>
                <div className="flex justify-between gap-8 items-center border-b border-white/5 pb-2">
                    <span className="flex items-center gap-2 text-white"><Keyboard size={10} /> WASD</span>
                    <span>Move</span>
                </div>
                <div className="flex justify-between gap-8 items-center border-b border-white/5 pb-2">
                    <span className="flex items-center gap-2 text-white"><Keyboard size={10} /> QE</span>
                    <span>Up / Down</span>
                </div>
                <div className="flex justify-between gap-8 items-center border-b border-white/5 pb-2">
                    <span className="flex items-center gap-2 text-white"><Keyboard size={10} /> SHIFT</span>
                    <span>Neural Sprint</span>
                </div>
                <div className="flex justify-between gap-8 items-center border-b border-white/5 pb-2">
                    <span className="flex items-center gap-2 text-white"><MousePointer2 size={10} /> LEFT CLICK</span>
                    <span>Signal Lock</span>
                </div>
                <div className="flex justify-between gap-8 items-center border-b border-white/5 pb-2">
                    <span className="flex items-center gap-2 text-white"><MousePointer2 size={10} /> RIGHT CLICK</span>
                    <span className="text-[#ff0055]">Emergency Purge</span>
                </div>
                <div className="flex justify-between gap-8 items-center pt-2">
                    <span className="flex items-center gap-2 text-white"><Keyboard size={10} /> ESC</span>
                    <span>Unlock Cursor</span>
                </div>
            </div>

            <div className="absolute bottom-12 left-12 z-50 flex flex-col gap-3 p-4 bg-black/40 border border-white/10 backdrop-blur-3xl rounded-sm font-bold">
                <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-[#ff0055]" />
                    <span className="text-[8px] tracking-[0.2em] text-white/60 uppercase">◈ North Star (Favorite)</span>
                </div>
                <div className="flex items-center gap-3 ml-4 border-l border-white/10 pl-3">
                    <div className="h-[1px] w-4 bg-[#ff0055]" />
                    <span className="text-[7px] tracking-[0.2em] text-white/40 uppercase italic">Favorite Constellation</span>
                </div>
                <div className="flex items-center gap-3 mt-1">
                    <div className="h-2 w-2 rounded-full bg-[#bc13fe]" />
                    <span className="text-[8px] tracking-[0.2em] text-white/60 uppercase">⚡ Neural Pulse (Recent)</span>
                </div>
                <div className="flex items-center gap-3 ml-4 border-l border-white/10 pl-3">
                    <div className="h-[1px] w-4 bg-[#bc13fe]" />
                    <span className="text-[7px] tracking-[0.2em] text-white/40 uppercase italic">Recent Constellation</span>
                </div>
                <div className="flex items-center gap-3 mt-1">
                    <div className="h-2 w-2 rounded-full bg-[#00ff88]" />
                    <span className="text-[8px] tracking-[0.2em] text-white/60 uppercase font-bold">● Neural Log (Seen)</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-[#ffaa00]" />
                    <span className="text-[8px] tracking-[0.2em] text-white/60 uppercase font-bold">⌬ Similar Signal (Neighbor)</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-[#00ffff]" />
                    <span className="text-[8px] tracking-[0.2em] text-white/60 uppercase font-bold">Active Signal (Target)</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-white" />
                    <span className="text-[8px] tracking-[0.2em] text-white/60 uppercase font-bold">Undiscovered Galaxy</span>
                </div>
            </div>

            {!loading && (
                <ForceGraph3D
                    ref={fgRef}
                    graphData={data}
                    backgroundColor="#000000"
                    showNavInfo={false}
                    nodeLabel={node => node.name}
                    onNodeClick={highlightMovie}
                    onNodeHover={handleNodeHover}
                    enablePointerInteraction={!isLocked}
                    linkColor={l => {
                        if (l.type === 'favorite') return '#ff0055';
                        if (l.type === 'recent') return '#bc13fe';
                        return 'transparent';
                    }}
                    linkWidth={2}
                    nodeRelSize={0.15}
                    nodeColor={n => {
                        if (selectedNode && n.id === selectedNode.id) return '#00ffff';
                        if (neighborIds.has(n.id)) return '#ffaa00';
                        if (n.type === 'favorite') return '#ff0055';
                        if (n.type === 'recent') return '#bc13fe';
                        if (n.type === 'watched') return '#00ff88';
                        return '#ffffff';
                    }}
                    forceEngine="none"
                />
            )}
        </main>
    );
}
