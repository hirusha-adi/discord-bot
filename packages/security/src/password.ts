import { randomBytes } from "node:crypto";
import argon2 from "argon2";
import bcrypt from "bcryptjs";

export function generatePassword(length = 18): string {
    return randomBytes(length).toString("base64url");
}

export async function hashPassword(password: string): Promise<string> {
    try {
        return await argon2.hash(password, {
            type: argon2.argon2id,
            timeCost: 3,
            memoryCost: 64 * 1024,
            parallelism: 1,
        });
    } catch {
        return bcrypt.hash(password, 12);
    }
}

export async function verifyPassword(hash: string, password: string): Promise<boolean> {
    if (hash.startsWith("$argon2")) {
        return argon2.verify(hash, password);
    }
    return bcrypt.compare(password, hash);
}
