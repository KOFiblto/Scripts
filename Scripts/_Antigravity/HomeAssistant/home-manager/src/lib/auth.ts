import { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

export const authOptions: NextAuthOptions = {
    providers: [
        CredentialsProvider({
            name: 'Credentials',
            credentials: {
                password: { label: "Password", type: "password" }
            },
            async authorize(credentials, req) {
                if (credentials?.password === process.env.ADMIN_PASSWORD) {
                    return { id: "1", name: "Admin", email: "admin@example.com" }
                }
                return null
            }
        })
    ],
    session: {
        strategy: "jwt",
    },
    secret: process.env.NEXTAUTH_SECRET,
}
