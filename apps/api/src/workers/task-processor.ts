import { prisma } from "../db.js";

export async function processDueTasks(limit = 50): Promise<number> {
    const due = await prisma.scheduledTask.findMany({
        where: {
            status: "PENDING",
            executeAt: { lte: new Date() },
        },
        take: limit,
        orderBy: { executeAt: "asc" },
    });

    for (const task of due) {
        try {
            await prisma.scheduledTask.update({
                where: { id: task.id },
                data: { status: "RUNNING", attempts: { increment: 1 } },
            });

            await prisma.auditLog.create({
                data: {
                    guildId: task.guildId,
                    actorType: "SYSTEM",
                    actorId: "worker",
                    action: `TASK_EXECUTED_${task.taskType}`,
                    targetType: "ScheduledTask",
                    targetId: task.id,
                    metadataJson: task.payloadJson,
                },
            });

            await prisma.scheduledTask.update({
                where: { id: task.id },
                data: { status: "COMPLETED" },
            });
        } catch (error) {
            await prisma.scheduledTask.update({
                where: { id: task.id },
                data: {
                    status: task.attempts + 1 >= task.maxAttempts ? "FAILED" : "PENDING",
                    lastError: error instanceof Error ? error.message : String(error),
                },
            });
        }
    }

    return due.length;
}
