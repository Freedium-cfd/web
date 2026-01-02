import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export type WithElementRef<
	T = Record<string, unknown>,
	E extends HTMLElement = HTMLElement,
> = T & {
	ref?: E | null;
};

export type WithoutChildrenOrChild<T> = T extends { children?: unknown }
	? Omit<T, "children" | "child">
	: T;

export type WithoutChild<T> = T extends { child?: unknown } ? Omit<T, "child"> : T;

export type WithoutChildren<T> = T extends { children?: unknown } ? Omit<T, "children"> : T;
