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
        src = { selectedDevice.qrCodePath }
                                            alt = "QR Code"
    fill
    className = "object-contain"
        />
                                    </div >
                                </div >
                            </div >
                        )
}

{
    selectedDevice?.pinCode && (
        <div className="space-y-2">
            <Label className="flex items-center gap-2 text-muted-foreground">
                <Lock className="w-3 h-3" />
                <span className="text-xs font-bold uppercase tracking-wider">PIN Code</span>
            </Label>
            <div className="flex items-center gap-2">
                <div className="font-mono text-lg bg-muted p-2 px-4 rounded border flex-1 text-center tracking-widest">
                    {showPin ? selectedDevice.pinCode : "••••••••"}
                </div>
                <Button variant="outline" size="icon" onClick={() => setShowPin(!showPin)}>
                    {showPin ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
            </div>
        </div>
    )
}
                    </div >

    <SheetFooter className="mt-6">
        <Button variant="destructive" className="w-full gap-2" onClick={handleDelete}>
            <Trash2 className="w-4 h-4" />
            Delete Device
        </Button>
    </SheetFooter>
                </SheetContent >
            </Sheet >
        </>
    )
}
