import { env } from "$env/dynamic/public";

const API_URL = env.PUBLIC_API_URL || "http://localhost:7080/api";

export default {
	API_URL,
};
