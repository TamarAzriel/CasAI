const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:5000";

export type Recommendation = {
  item_name?: string;
  item_price?: string | number;
  image_url?: string;
  product_link?: string;
  similarity?: number;
  item_cat?: string;
  [key: string]: unknown;
};

type BackendError = { error?: string };

async function handleResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: BackendError | T;

  try {
    data = text ? (JSON.parse(text) as BackendError | T) : ({} as T);
  } catch {
    throw new Error(`Unexpected response from server (status ${response.status})`);
  }

  if (!response.ok) {
    const message = (data as BackendError).error ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data as T;
}

export async function recommendByText(query: string): Promise<Recommendation[]> {
  const response = await fetch(`${API_BASE_URL}/recommend/text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  return handleResponse<Recommendation[]>(response);
}

export async function recommendByImage(params: { image: File; text?: string }): Promise<Recommendation[]> {
  const formData = new FormData();
  formData.append("image", params.image);
  if (params.text?.trim()) {
    formData.append("text", params.text.trim());
  }

  const response = await fetch(`${API_BASE_URL}/recommend/image`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<Recommendation[]>(response);
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

