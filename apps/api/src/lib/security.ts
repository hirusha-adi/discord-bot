import { createHash, randomBytes } from "node:crypto";
import argon2 from "argon2";
import bcrypt from "bcryptjs";

export function createSessionToken(): string {
    return randomBytes(32).toString("base64url");
}

export function hashSessionToken(token: string): string {
    return createHash("sha256").update(token).digest("hex");
}

export async function verifyPassword(hash: string, password: string): Promise<boolean> {
    if (hash.startsWith("$argon2")) {
        return argon2.verify(hash, password);
    }
    return bcrypt.compare(password, hash);
}
