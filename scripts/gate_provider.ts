// Dedicated gate provider. Keeps the frozen harness away from services already
// using port 8080 while preserving every normally discovered Neura extension.
export default function (pi) {
  const baseUrl = process.env.MASTER_MODELS_GATE_BASE_URL ?? "http://127.0.0.1:18080/v1";

  pi.registerProvider("master-models-gate", {
    name: "Master Models Gate (llama.cpp)",
    baseUrl,
    apiKey: "sk-local",
    api: "openai-completions",
    models: [
      {
        id: "frontend-stack-gate",
        name: "Frontend Stack Gate Model",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 16384,
        maxTokens: 8192,
      },
    ],
  });
}
