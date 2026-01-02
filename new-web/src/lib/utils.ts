import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { WithElementRef as BitsWithElementRef } from "bits-ui";
import type { Snippet } from "svelte";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export type WithElementRef<
	T extends Record<string, unknown> = Record<string, unknown>,
	E extends Element = HTMLElement,
> = BitsWithElementRef<T, E>;

export type WithoutChildrenOrChild<T> = T extends { children?: unknown }
	? Omit<T, "children" | "child">
	: T;

export type WithoutChild<T> = T extends { child?: unknown } ? Omit<T, "child"> : T;

export type WithoutChildren<T> = T extends { children?: unknown } ? Omit<T, "children"> : T;
