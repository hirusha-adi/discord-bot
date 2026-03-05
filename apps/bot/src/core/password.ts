import { randomBytes } from "node:crypto";
import argon2 from "argon2";
import bcrypt from "bcryptjs";

export async function hashPassword(plainTextPassword: string): Promise<string> {
    try {
        return await argon2.hash(plainTextPassword, {
            type: argon2.argon2id,
            timeCost: 3,
            memoryCost: 64 * 1024,
            parallelism: 1,
        });
    } catch {
        return bcrypt.hash(plainTextPassword, 12);
    }
}

export function generateSecurePassword(length = 24): string {
    return randomBytes(length).toString("base64url");
}
