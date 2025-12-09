'use client'

import { useState } from 'react'
import { Device } from '@prisma/client'
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { updateDevice, deleteDevice } from "@/actions/devices"
import { Loader2, Trash2 } from "lucide-react"

interface DeviceEditDialogProps {
    device: Device
    open: boolean
    onOpenChange: (open: boolean) => void
    trigger?: React.ReactNode
}

export function DeviceEditDialog({ device, open, onOpenChange, trigger }: DeviceEditDialogProps) {
    const [isLoading, setIsLoading] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setIsLoading(true)

        try {
            const formData = new FormData(event.currentTarget)
            formData.append('id', device.id)
            formData.append('floorplanId', device.floorplanId)

            await updateDevice(formData)
            onOpenChange(false)
        } catch (error) {
            console.error(error)
        } finally {
            setIsLoading(false)
        }
    }

    async function handleDelete() {
        if (!confirm("Are you sure you want to delete this device?")) return
        setIsDeleting(true)
        try {
            await deleteDevice(device.id, device.floorplanId)
            onOpenChange(false)
        } catch (error) {
            console.error(error)
        } finally {
            setIsDeleting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Edit Device</DialogTitle>
                    <DialogDescription>
                        Make changes to your device here. Click save when you're done.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={onSubmit}>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="name" className="text-right">
                                Name
                            </Label>
                            <Input id="name" name="name" defaultValue={device.name} className="col-span-3" required />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="type" className="text-right">
                                Type
                            </Label>
                            <Select name="type" defaultValue={device.type}>
                                <SelectTrigger className="col-span-3">
                                    <SelectValue placeholder="Select type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="switch">Switch</SelectItem>
                                    <SelectItem value="light">Light</SelectItem>
                                    <SelectItem value="sensor">Sensor</SelectItem>
                                    <SelectItem value="camera">Camera</SelectItem>
                                    <SelectItem value="thermostat">Thermostat</SelectItem>
                                    <SelectItem value="lock">Lock</SelectItem>
                                    <SelectItem value="media">Media Player</SelectItem>
                                    <SelectItem value="alarm_control_panel">Alarm System</SelectItem>
                                    <SelectItem value="button">Button</SelectItem>
                                    <SelectItem value="flood_sensor">Flood Sensor</SelectItem>
                                    <SelectItem value="motion_sensor">Motion Sensor</SelectItem>
                                    <SelectItem value="power_outlet">Power Outlet</SelectItem>
                                    <SelectItem value="roller_shutter">Roller Shutter</SelectItem>
                                    <SelectItem value="window_door_sensor">Window/Door Sensor</SelectItem>
                                    <SelectItem value="unknown">Unknown</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="protocol" className="text-right">
                                Protocol
                            </Label>
                            <Select name="protocol" defaultValue={device.protocol}>
                                <SelectTrigger className="col-span-3">
                                    <SelectValue placeholder="Select protocol" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="zigbee">Zigbee</SelectItem>
                                    <SelectItem value="zwave">Z-Wave</SelectItem>
                                    <SelectItem value="wifi">WiFi</SelectItem>
                                    <SelectItem value="thread">Thread</SelectItem>
                                    <SelectItem value="matter">Matter</SelectItem>
                                    <SelectItem value="bluetooth">Bluetooth</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="description" className="text-right">
                                Description
                            </Label>
                            <Input id="description" name="description" defaultValue={device.description || ''} className="col-span-3" />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="pinCode" className="text-right">
                                PIN Code
                            </Label>
                            <Input id="pinCode" name="pinCode" defaultValue={device.pinCode || ''} className="col-span-3" placeholder="Optional" />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="qrFile" className="text-right">
                                New QR Code
                            </Label>
                            <Input id="qrFile" name="qrFile" type="file" className="col-span-3" accept="image/*" />
                        </div>
                    </div>
                    <DialogFooter className="flex justify-between sm:justify-between">
                        <Button type="button" variant="destructive" onClick={handleDelete} disabled={isDeleting || isLoading}>
                            {isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Trash2 className="mr-2 h-4 w-4" />}
                            Delete
                        </Button>
                        <Button type="submit" disabled={isLoading || isDeleting}>
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save changes
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
