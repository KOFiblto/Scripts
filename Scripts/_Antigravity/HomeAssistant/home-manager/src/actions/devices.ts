'use server'

import { prisma } from "@/lib/prisma"
import { saveFile } from "@/lib/storage"
import { revalidatePath } from "next/cache"

export async function createDevice(formData: FormData) {
    const floorplanId = formData.get('floorplanId') as string
    const name = formData.get('name') as string
    const description = formData.get('description') as string
    const type = formData.get('type') as string
    const protocol = formData.get('protocol') as string
    const pinCode = formData.get('pinCode') as string
    const qrFile = formData.get('qrFile') as File | null

    if (!name || !floorplanId || !protocol) {
        throw new Error("Missing required fields")
    }

    let qrCodePath = null
    if (qrFile && qrFile.size > 0 && qrFile.name !== 'undefined') {
        qrCodePath = await saveFile(qrFile, 'qrcodes')
    }

    await prisma.device.create({
        data: {
            floorplanId,
            name,
            description,
            type: type || 'switch', // Default or required
            protocol,
            pinCode,
            qrCodePath,
            xPos: 50,
            yPos: 50
        }
    })

    revalidatePath(`/dashboard/floorplans/${floorplanId}`)
    return { success: true }
}

export async function deleteDevice(id: string, floorplanId: string) {
    await prisma.device.delete({ where: { id } })
    revalidatePath(`/dashboard/floorplans/${floorplanId}`)
    return { success: true }
}

export async function updateDevice(formData: FormData) {
    const id = formData.get('id') as string
    const floorplanId = formData.get('floorplanId') as string
    const name = formData.get('name') as string
    const description = formData.get('description') as string
    const type = formData.get('type') as string
    const protocol = formData.get('protocol') as string
    const pinCode = formData.get('pinCode') as string
    const qrFile = formData.get('qrFile') as File | null

    if (!id || !name || !protocol) {
        throw new Error("Missing required fields")
    }

    const data: any = {
        name,
        description,
        type,
        protocol,
        pinCode
    }

    if (qrFile && qrFile.size > 0 && qrFile.name !== 'undefined') {
        const qrCodePath = await saveFile(qrFile, 'qrcodes')
        data.qrCodePath = qrCodePath
    }

    await prisma.device.update({
        where: { id },
        data
    })

    revalidatePath(`/dashboard/floorplans/${floorplanId}`)
    revalidatePath('/dashboard/devices')
    return { success: true }
}
