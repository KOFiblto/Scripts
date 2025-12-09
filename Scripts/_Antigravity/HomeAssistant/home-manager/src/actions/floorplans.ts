'use server'

import { prisma } from "@/lib/prisma"
import { saveFile } from "@/lib/storage"
import { revalidatePath } from "next/cache"

export async function createFloorplan(formData: FormData) {
    const name = formData.get('name') as string
    const file = formData.get('file') as File

    // Handling image dimensions might be tricky if not sent from client.
    // The plan says: "Floorplan (id, name, imagePath, width, height, createdAt)".
    // Step 2 says: "Floorplan (..., width, height, ...)"
    // The form submission in Step 4 says: "handle the form submission ... write the record".
    // Usually, we'd read dimensions from the file or have client send them.
    // I will assume for now the client sends them or we default to 0 and update later?
    // Or maybe I can use 'image-size' lib or similar.
    // But plan Step 4 just says "handle form submission".
    // Step 5 says "Add an 'Add Floorplan' card that opens a Dialog with a file input. Connect this form to the createFloorplan Server Action."
    // It doesn't explicitly mention width/height inputs.
    // But Konva needs them.
    // I will read width/height from the FormData, assuming the client handles reading it (e.g. loading image into hidden img tag to get size).

    const widthStr = formData.get('width')
    const heightStr = formData.get('height')

    const width = widthStr ? parseFloat(widthStr as string) : 800 // Default or throw
    const height = heightStr ? parseFloat(heightStr as string) : 600

    if (!name || !file) {
        throw new Error("Missing fields")
    }

    const imagePath = await saveFile(file, 'floorplans')

    await prisma.floorplan.create({
        data: {
            name,
            imagePath,
            width,
            height
        }
    })

    revalidatePath('/dashboard/floorplans')
    return { success: true }
}


