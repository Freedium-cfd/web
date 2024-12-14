import { env } from "$env/dynamic/public";

const API_URL = env.VITE_API_URL || "http://localhost:7080/api";

export default {
	API_URL,
};
