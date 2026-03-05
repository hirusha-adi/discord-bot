import { loadApiEnvironment } from "../load-env.js";
import { processDueTasks } from "./task-processor.js";

loadApiEnvironment();

async function runLoop() {
    while (true) {
        const processed = await processDueTasks();
        if (processed > 0) {
            console.log(`Processed ${processed} scheduled tasks.`);
        }

        await new Promise((resolve) => setTimeout(resolve, 5000));
    }
}

runLoop().catch((error) => {
    console.error("Worker loop failed", error);
    process.exit(1);
});
