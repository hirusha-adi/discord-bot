import { buildApiApp } from "./app.js";
import { config } from "./config.js";

const app = await buildApiApp();

app.listen({
    host: config.host,
    port: config.port,
}).then(() => {
    app.log.info(`API listening on ${config.host}:${config.port}`);
}).catch((error) => {
    app.log.error(error);
    process.exit(1);
});
