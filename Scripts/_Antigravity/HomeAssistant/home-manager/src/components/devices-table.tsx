'use client'

import Link from "next/link"
import { IconImage } from "@/components/icon-image"
import { DeviceEditDialog } from "@/components/device-edit-dialog"
import { useState } from "react"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export function DevicesTable({ devices }: { devices: any[] }) {
    return (
        <div className="container mx-auto py-10">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">All Devices</h1>
            </div>

            <div className="border rounded-lg overflow-hidden">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[50px]">Icon</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Protocol</TableHead>
                            <TableHead>Floorplan</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {devices.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                                    No devices found. Add devices from a floorplan.
                                </TableCell>
                            </TableRow>
                        ) : (
                            devices.map((device) => (
                                <DeviceRow key={device.id} device={device} />
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}

function DeviceRow({ device }: { device: any }) {
    const [open, setOpen] = useState(false)
    return (
        <TableRow>
            <TableCell>
                <div className="relative w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center overflow-hidden border">
                    <IconImage
                        type={device.type}
                        protocol={device.protocol}
                        className="p-1"
                    />
                </div>
            </TableCell>
            <TableCell className="font-medium">{device.name}</TableCell>
            <TableCell className="capitalize">{device.type}</TableCell>
            <TableCell>
                <Badge variant="secondary" className="capitalize">
                    {device.protocol}
                </Badge>
            </TableCell>
            <TableCell>
                <Link href={`/dashboard/floorplans/${device.floorplan.id}`} className="hover:underline text-blue-500">
                    {device.floorplan.name}
                </Link>
            </TableCell>
            <TableCell className="text-right">
                <DeviceEditDialog
                    device={device}
                    open={open}
                    onOpenChange={setOpen}
                    trigger={<Button variant="ghost" size="sm">Edit</Button>}
                />
            </TableCell>
        </TableRow>
    )
}
