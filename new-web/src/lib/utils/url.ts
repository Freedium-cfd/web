/**
 * Normalize an article slug/path back to a full URL (https://...).
 *
 * SvelteKit collapses double slashes `//` in route params, converting
 * `https://host.com/path` into `https:/host.com/path`.
 * This restores the double slash and adds https:// if missing.
 */
export function toOriginalUrl(raw: string): string | null {
	if (!raw) return null;
	const s = raw.trim().replace(/^(https?):\/+(?!\/)/i, "$1://");
	if (/^https?:\/\//i.test(s)) return s;
	if (s.includes(".") && !s.includes(" ")) return `https://${s}`;
	return null;
}
