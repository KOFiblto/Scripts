'use client'

import { useState, useEffect } from "react"
import { Floorplan, Device } from "@prisma/client"
import { MapEditor } from "./map-editor"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Lock, Unlock } from "lucide-react"
import { DeviceEditDialog } from "./device-edit-dialog"

interface FloorplanViewerProps {
    floorplan: Floorplan
    devices: Device[]
}

export function FloorplanViewer({ floorplan, devices }: FloorplanViewerProps) {
    const [isLocked, setIsLocked] = useState(false)
    const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)
    const [editDialogOpen, setEditDialogOpen] = useState(false)

    // Sync selectedDevice with dialog open state
    useEffect(() => {
        if (selectedDevice) {
            setEditDialogOpen(true)
        }
    }, [selectedDevice])

    // When dialog closes, clear selection
    const handleOpenChange = (open: boolean) => {
        setEditDialogOpen(open)
        if (!open) {
            setSelectedDevice(null)
        }
    }

    return (
        <div className="h-full flex flex-col">
            <div className="p-4 border-b flex justify-between items-center bg-card">
                <h1 className="text-2xl font-bold">{floorplan.name}</h1>
                <div className="flex items-center gap-2">
                    <div className="flex items-center space-x-2">
                        <Label htmlFor="lock-mode">{isLocked ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}</Label>
                        <Switch id="lock-mode" checked={isLocked} onCheckedChange={setIsLocked} />
                    </div>
                </div>
            </div>
            <div className="flex-1 overflow-hidden relative">
                <MapEditor
                    floorplan={floorplan}
                    devices={devices}
                    onDeviceClick={setSelectedDevice}
                    isLocked={isLocked}
                />

                {selectedDevice && (
                    <DeviceEditDialog
                        device={selectedDevice}
                        open={editDialogOpen}
                        onOpenChange={handleOpenChange}
                    />
                )}
            </div>
        </div>
    )
}
