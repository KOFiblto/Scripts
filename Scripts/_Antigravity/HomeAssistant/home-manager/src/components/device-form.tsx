'use client'

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { createDevice } from "@/actions/devices"

interface DeviceFormProps {
    floorplanId: string
    onSuccess?: () => void
}

export function DeviceForm({ floorplanId, onSuccess }: DeviceFormProps) {
    const [loading, setLoading] = useState(false)

    async function handleSubmit(formData: FormData) {
        setLoading(true)
        formData.append('floorplanId', floorplanId)
        await createDevice(formData)
        setLoading(false)
        if (onSuccess) onSuccess()
    }

    return (
        <form action={handleSubmit} className="space-y-4">
            <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" name="name" placeholder="Living Room Light" required />
            </div>

            <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea id="description" name="description" placeholder="Main ceiling light..." />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="type">Device Type</Label>
                    <Select name="type" required>
                        <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="switch">Switch / Light</SelectItem>
                            <SelectItem value="power_outlet">Power Outlet</SelectItem>
                            <SelectItem value="button">Button</SelectItem>
                            <SelectItem value="sensor">Sensor (Generic)</SelectItem>
                            <SelectItem value="motion_sensor">Motion Sensor</SelectItem>
                            <SelectItem value="flood_sensor">Flood Sensor</SelectItem>
                            <SelectItem value="window-door_sensor">Window/Door Sensor</SelectItem>
                            <SelectItem value="camera">Camera</SelectItem>
                            <SelectItem value="alarm_system">Alarm System</SelectItem>
                            <SelectItem value="roller_shutter">Roller Shutter</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="protocol">Protocol</Label>
                    <Select name="protocol" defaultValue="zigbee">
                        <SelectTrigger>
                            <SelectValue placeholder="Select protocol" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="zigbee">Zigbee</SelectItem>
                            <SelectItem value="zwave">Z-Wave</SelectItem>
                            <SelectItem value="matter">Matter</SelectItem>
                            <SelectItem value="wifi">WiFi</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="space-y-2">
                <Label htmlFor="pinCode">PIN Code</Label>
                <Input id="pinCode" name="pinCode" type="password" placeholder="1234" />
            </div>

            <div className="space-y-2">
                <Label htmlFor="qrFile">QR Code Image</Label>
                <Input id="qrFile" name="qrFile" type="file" accept="image/*" />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Adding Device...' : 'Add Device'}
            </Button>
        </form>
    )
}
