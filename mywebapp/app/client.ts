import type { paths } from "./api";
import createClient from "openapi-fetch";

export const client = createClient<paths>({ baseUrl: "http://localhost:8000" });