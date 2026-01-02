import { ofetch } from "ofetch";
import config from "./config";

const apiFetch = ofetch.create({
	baseURL: config.API_URL,
});

export default apiFetch;
