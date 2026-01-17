import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: string | number | undefined | null) {
  if (price === undefined || price === null || price === "N/A") return "N/A";
  const priceStr = String(price).trim();
  if (priceStr.startsWith("₪")) return priceStr;
  return `₪ ${priceStr}`;
}