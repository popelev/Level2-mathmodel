/**
 * TypeScript BFF placeholder — Wave 1 mock server entry.
 * Runtime mocks: `npm run start` → src/server.ts (OpenAPI-shaped).
 */
export { startServer } from "./server.js";
export const serviceName = "level2-mathmodel-api-mock";

export function ping(): string {
  return "ok";
}
