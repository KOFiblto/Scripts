'use server'

import { prisma } from "@/lib/prisma"
import { revalidatePath } from "next/cache"

export async function updateDevicePosition(id: string, xPos: number, yPos: number, floorplanId: string) {
    await prisma.device.update({
        where: { id },
        data: { xPos, yPos }
    })

    revalidatePath(`/dashboard/floorplans/${floorplanId}`)
    return { success: true }
}

export async function updateDeviceScale(deviceId: string, scale: number) {
    try {
        await prisma.device.update({
            where: { id: deviceId },
            data: { scale }
        })
        revalidatePath('/dashboard/floorplans')
    } catch (error) {
        console.error('Failed to update device scale:', error)
        throw new Error('Failed to update device scale')
    }
}
