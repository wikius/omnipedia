// utils/dataLoader.ts

import { DataSet, AllData, dataCache } from "./cache";

/**
 * Retrieves the DataSet for a given key.
 * @param key - The key representing the dataset to retrieve (e.g., 'ABCC11', 'APRT').
 * @returns The corresponding DataSet or null if the key doesn't exist.
 */
export function getData(key: string): DataSet | null {
  const data: AllData = dataCache;

  if (data[key]) {
    return data[key];
  } else {
    console.error(`Data for key "${key}" not found.`);
    return null;
  }
}
