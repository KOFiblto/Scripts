'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Stage, Layer, Image as KonvaImage, Circle, Group, Text, Rect, Transformer } from 'react-konva'
import useImage from 'use-image'
import { Floorplan, Device } from '@prisma/client'
import { updateDevicePosition, updateDeviceScale } from '@/actions/device-positions'
// Removed Lucide imports as we are not using them for Konva rendering currently.

// Helper to check collision with drag
function getDistance(p1: { x: number, y: number }, p2: { x: number, y: number }) {
    return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2))
}

interface MapEditorProps {
    floorplan: Floorplan
    devices: Device[]
    onDeviceClick?: (device: Device) => void
    isLocked?: boolean
}

// Generate color from string
const stringToColor = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const c = (hash & 0x00ffffff).toString(16).toUpperCase();
    return '#' + "00000".substring(0, 6 - c.length) + c;
}

const DeviceNode = ({ device, floorplanWidth, floorplanHeight, onDragEnd, onTransformEnd, onClick, scale, draggable, isSelected, isLocked }: any) => {
    const x = ((device.xPos ?? 50) / 100) * floorplanWidth
    const y = ((device.yPos ?? 50) / 100) * floorplanHeight

    const color = stringToColor(device.id + device.name)

    // Protocol badge text fallback
    const protocolCode = device.protocol?.charAt(0).toUpperCase() || '?'

    // Icon Path (Device Type)
    const iconPath = `/assets/icons/devices/${device.type?.toLowerCase()}.png`
    const [iconImage] = useImage(iconPath)

    // Protocol Icon Path
    const protocolPath = `/assets/icons/protocols/${device.protocol?.toLowerCase()}.png`
    const [protocolImage] = useImage(protocolPath)

    const invScale = 1 / scale

    // Geometry Constants
    const pillHeight = 44 * invScale // Taller to fit 2 lines if needed
    const pillWidth = 160 * invScale
    const iconRadius = 14 * invScale

    // Icon 1 (Device)
    const icon1CenterX = 22 * invScale

    // Icon 2 (Protocol)
    const icon2CenterX = icon1CenterX + (28 * invScale) + (4 * invScale) // Adjacent with small gap

    // Text
    const textX = icon2CenterX + iconRadius + (8 * invScale)
    const textWidth = pillWidth - textX - (8 * invScale)

    const shapeRef = React.useRef<any>(null)
    const trRef = React.useRef<any>(null)

    React.useEffect(() => {
        if (isSelected && !isLocked) {
            // we need to attach transformer manually
            trRef.current?.nodes([shapeRef.current]);
            trRef.current?.getLayer()?.batchDraw();
        }
    }, [isSelected, isLocked]);

    return (
        <>
            <Group
                ref={shapeRef}
                x={x}
                y={y}
                // Use saved scale. Note: Konva handles scaleX/scaleY.
                // If we saved it as 1.2, we apply it here.
                scaleX={device.scale || 1}
                scaleY={device.scale || 1}
                draggable={draggable}
                onDragEnd={(e) => {
                    const newX = e.target.x()
                    const newY = e.target.y()
                    onDragEnd(device.id, newX, newY)
                }}
                onTransformEnd={(e) => {
                    // transformer is changing scaleX and scaleY and rotation
                    const node = shapeRef.current;
                    const scaleX = node.scaleX();
                    // We update DB with new scale
                    // Reset node scale to 1 in generic state but passed up? 
                    // Actually usually we just persist the scale.
                    (onTransformEnd as any)?.(device.id, scaleX);
                }}
                onClick={() => onClick?.(device)}
                onTap={() => onClick?.(device)}
                onMouseEnter={(e) => {
                    if (!draggable) return
                    const container = e.target.getStage()?.container();
                    if (container) container.style.cursor = 'move';
                }}
                onMouseLeave={(e) => {
                    const container = e.target.getStage()?.container();
                    if (container) container.style.cursor = 'default';
                }}
            >
                {/* Background Pill */}
                <Rect
                    width={pillWidth}
                    height={pillHeight}
                    x={0}
                    y={-pillHeight / 2}
                    cornerRadius={pillHeight / 2}
                    fill={color}
                    shadowColor="black"
                    shadowBlur={5}
                    shadowOpacity={0.3}
                />

                {/* --- Device Type Icon (Leftmost) --- */}
                {/* Removed white circle background so it matches pill color */}

                {iconImage ? (
                    <KonvaImage
                        image={iconImage}
                        x={icon1CenterX - iconRadius}
                        y={-iconRadius}
                        width={iconRadius * 2}
                        height={iconRadius * 2}
                    />
                ) : (
                    <Circle
                        x={icon1CenterX}
                        y={0}
                        radius={iconRadius}
                        fill="rgba(255,255,255,0.2)" // Slight highlight if missing
                    />
                )}

                {!iconImage && (
                    <Text
                        text="?"
                        x={icon1CenterX - (4 * invScale)}
                        y={-(6 * invScale)}
                        fontSize={12 * invScale}
                        fill="white"
                    />
                )}

                {/* --- Protocol Icon (Next to Device) --- */}

                {protocolImage ? (
                    <KonvaImage
                        image={protocolImage}
                        x={icon2CenterX - iconRadius}
                        y={-iconRadius}
                        width={iconRadius * 2}
                        height={iconRadius * 2}
                    />
                ) : (
                    // Only show text if image is missing
                    <Text
                        text={protocolCode}
                        x={icon2CenterX - (4 * invScale)}
                        y={-(6 * invScale)}
                        fontSize={12 * invScale}
                        fontStyle="bold"
                        fill="white"
                    />
                )}

                {/* --- Device Name (Remaining space) --- */}
                <Text
                    text={device.name}
                    x={textX}
                    y={-14 * invScale} // Start higher to allow wrapping
                    width={textWidth}
                    height={28 * invScale} // Constrain height
                    align="left"
                    verticalAlign="middle"
                    fontSize={11 * invScale}
                    fill="white"
                    fontStyle="bold"
                    wrap="word"
                    ellipsis={true}
                />
            </Group>

            {isSelected && !isLocked && (
                <Transformer
                    ref={trRef}
                    boundBoxFunc={(oldBox, newBox) => {
                        // limit resize if needed
                        if (newBox.width < 50 || newBox.height < 50) {
                            return oldBox;
                        }
                        return newBox;
                    }}
                    enabledAnchors={['top-left', 'top-right', 'bottom-left', 'bottom-right']}
                    rotateEnabled={false}
                />
            )}
        </>
    )
}

export function MapEditor({ floorplan, devices, onDeviceClick, isLocked = false }: MapEditorProps) {
    const containerRef = useRef<HTMLDivElement>(null)
    const wrapperRef = useRef<HTMLDivElement>(null)
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
    const [position, setPosition] = useState({ x: 0, y: 0, scale: 1 })

    // Local state for optimistic updates
    const [localDevices, setLocalDevices] = useState(devices)

    // Sync prop changes to local state
    useEffect(() => {
        setLocalDevices(devices)
    }, [devices])

    // Load floorplan image
    const [image] = useImage(floorplan.imagePath)

    useEffect(() => {
        if (!containerRef.current) return
        const updateSize = () => {
            const { clientWidth, clientHeight } = containerRef.current!
            setDimensions({ width: clientWidth, height: clientHeight })

            // Initial fit logic
            if (floorplan.width > 0 && floorplan.height > 0) {
                const scaleX = clientWidth / floorplan.width
                const scaleY = clientHeight / floorplan.height
                const fitScale = Math.min(scaleX, scaleY) * 0.9
                setPosition({
                    x: (clientWidth - floorplan.width * fitScale) / 2,
                    y: (clientHeight - floorplan.height * fitScale) / 2,
                    scale: fitScale
                })
            }
        }
        updateSize()
        window.addEventListener('resize', updateSize)
        return () => window.removeEventListener('resize', updateSize)
    }, [floorplan.width, floorplan.height])

    const handleWheel = (e: any) => {
        e.evt.preventDefault();
        const stage = e.target.getStage();
        const oldScale = stage.scaleX();

        const pointer = stage.getPointerPosition();
        const mousePointTo = {
            x: (pointer.x - stage.x()) / oldScale,
            y: (pointer.y - stage.y()) / oldScale,
        };

        const scaleBy = 1.1;
        const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;

        // Limit zoom
        if (newScale < 0.1 || newScale > 10) return;

        setPosition(prev => ({
            ...prev,
            scale: newScale,
            x: pointer.x - mousePointTo.x * newScale,
            y: pointer.y - mousePointTo.y * newScale,
        }));
    };

    const handleDragEnd = async (id: string, x: number, y: number) => {
        // x, y are in floorplan coordinate space?
        // Not if the Node is child of Layer (which is scaled).
        // Wait, if Node is child of Layer, and Stage is scaled/panned...
        // The x/y returned by Node.x() are relative to Layer.
        // If Layer is not transformed, but Stage is?
        // If Stage moves, everything moves properly visually.
        // The relative coordinates inside the layer should remain correct for calculations 
        // IF the drag logic handles the stage transform properly?
        // Konva 'draggable' on a node modifies its x/y properties relative to its parent.
        // If parent (Layer) is not scaled, then x/y = pixels.
        // We are scaling Stage. 
        // So Node x/y is still 0..width. (Local coordinates).
        // SO: We just normalize by floorplan width/height.

        // Convert stage coordinates back to percentage
        if (!dimensions.width || !dimensions.height) return
        const xPercent = (x / dimensions.width) * 100
        const yPercent = (y / dimensions.height) * 100

        // Optimistically update
        setLocalDevices(prev => prev.map(d => d.id === id ? { ...d, xPos: xPercent, yPos: yPercent } : d))

        try {
            await updateDevicePosition(id, xPercent, yPercent, floorplan.id)
        } catch (e) {
            console.error("Failed to update position")
        }
    }

    // Callback for scale end
    const handleTransformEnd = async (id: string, scaleX: number) => {
        // We only care about uniform scale for now, so X is fine.
        // We persist this scale factor.

        // Optimistically update
        setLocalDevices(prev => prev.map(d => d.id === id ? { ...d, scale: scaleX } : d))

        try {
            await updateDeviceScale(id, scaleX)
        } catch (e) {
            console.error("Failed to update scale")
        }
    }

    useEffect(() => {
        // Initial fit
        if (wrapperRef.current && dimensions.width > 0) {
            const containerWidth = wrapperRef.current.offsetWidth
            const scale = containerWidth / dimensions.width
            setPosition(p => ({ ...p, scale: scale, x: 0, y: 0 }))
        }
    }, [dimensions.width])

    // Device Selection for Click
    // When clicking a device, we select it for Transformer.
    // If clicking background, deselect.
    const [selectedId, setSelectedId] = useState<string | null>(null)

    const checkDeselect = (e: any) => {
        const clickedOnEmpty = e.target === e.target.getStage();
        if (clickedOnEmpty) {
            setSelectedId(null);
            // Trigger parent click for Deselect if needed
            onDeviceClick?.(null as any) // Hacky way to clear
        }
    };

    return (
        <div ref={containerRef} className="w-full h-full bg-slate-900 border overflow-hidden cursor-crosshair">
            <div ref={wrapperRef} className="w-full h-full">
                {dimensions.width > 0 && (
                    <Stage
                        width={containerRef.current?.offsetWidth || 800}
                        height={containerRef.current?.offsetHeight || 600}
                        draggable={!isLocked}
                        onWheel={handleWheel}
                        scaleX={position.scale}
                        scaleY={position.scale}
                        x={position.x}
                        y={position.y}
                        onMouseDown={checkDeselect}
                        onTouchStart={checkDeselect}
                    >
                        <Layer>
                            {floorplan.imagePath && (
                                <KonvaImage
                                    image={image}
                                    width={dimensions.width}
                                    height={dimensions.height}
                                />
                            )}
                            {localDevices.map(device => (
                                <DeviceNode
                                    key={device.id}
                                    device={device}
                                    floorplanWidth={dimensions.width}
                                    floorplanHeight={dimensions.height}
                                    onDragEnd={handleDragEnd}
                                    onTransformEnd={handleTransformEnd}
                                    onClick={(d: Device) => {
                                        setSelectedId(d.id)
                                        onDeviceClick?.(d)
                                    }}
                                    scale={position.scale}
                                    draggable={!isLocked}
                                    isSelected={selectedId === device.id}
                                    isLocked={isLocked}
                                />
                            ))}
                        </Layer>
                    </Stage>
                )}
            </div>
        </div>
    )
}
